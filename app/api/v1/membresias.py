import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from app.models.membresias import Membresias_periodo
from app.models.usuarios import User
from app.schemas.membership import (
    AssignmentCreate,
    AssignmentResponse,
    MembershipCreate,
    MembershipListResponse,
    MembershipResponse,
    MembershipUpdate,
)
from app.services.membership_service import (
    ActiveAssignmentExistsError,
    MembershipInactiveError,
    MembershipInUseError,
    MembershipNameExistsError,
    MembershipNotFoundError,
    MembershipService,
    UserNotFoundError,
)

# Roles que pueden gestionar membresías, ya normalizados
# (minúsculas, sin tildes, espacios ni guiones).
ADMIN_ROLES_NORMALIZED = {
    "superadministrador",
    "superadmin",
    "administrador",
    "admin",
}


def _normalize_role(role) -> str:
    """Convierte un rol (enum o texto) a una forma comparable.

    Ej.: Roles.SUPER_ADMIN, "Super Administrador" y "super_admin"
    se comparan de forma consistente.
    """
    if role is None:
        return ""

    # Si es un Enum se prueba con su valor; si no, con su representación.
    raw = str(getattr(role, "value", role))
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", raw.lower())


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    role = current_user.role
    candidates = {
        _normalize_role(role),
        # Por si el valor del enum y su nombre difieren.
        _normalize_role(getattr(role, "name", None)),
    }

    is_super_admin = getattr(current_user, "super_admin_slot", None) == 1

    if is_super_admin or candidates & ADMIN_ROLES_NORMALIZED:
        return current_user

    # Diagnóstico temporal: se ve en la terminal de uvicorn.
    print(f"[MEMBRESIAS] Acceso denegado. rol recibido: {role!r}")

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para gestionar membresías.",
    )


router = APIRouter(
    prefix="/membresias",
    tags=["Membresías"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=MembershipListResponse)
def list_memberships(
    search: str | None = Query(default=None, max_length=100),
    is_active: bool | None = None,
    period: Membresias_periodo | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista las membresías con filtros y paginación."""
    items, total = MembershipService.list_memberships(
        db,
        search=search,
        is_active=is_active,
        period=period,
        page=page,
        page_size=page_size,
    )
    return MembershipListResponse(
        items=[MembershipResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{membership_id}", response_model=MembershipResponse)
def get_membership(
    membership_id: int,
    db: Session = Depends(get_db),
):
    """Devuelve una membresía por su id."""
    try:
        return MembershipService.get_membership(db, membership_id)
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )


@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_membership(
    data: MembershipCreate,
    db: Session = Depends(get_db),
):
    """Crea una membresía."""
    try:
        return MembershipService.create_membership(db, data)
    except MembershipNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


@router.patch("/{membership_id}", response_model=MembershipResponse)
def update_membership(
    membership_id: int,
    data: MembershipUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente una membresía (solo los campos enviados)."""
    try:
        return MembershipService.update_membership(db, membership_id, data)
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except MembershipNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(
    membership_id: int,
    db: Session = Depends(get_db),
):
    """Elimina una membresía que no tenga asignaciones."""
    try:
        MembershipService.delete_membership(db, membership_id)
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except MembershipInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{membership_id}/asignaciones",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_membership(
    membership_id: int,
    data: AssignmentCreate,
    db: Session = Depends(get_db),
):
    """Asigna una membresía a un cliente."""
    try:
        return MembershipService.assign_membership(db, membership_id, data)
    except (MembershipNotFoundError, UserNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except MembershipInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except ActiveAssignmentExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
