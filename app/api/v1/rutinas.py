from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.api.v1.membresias import _normalize_role
from app.infrastructure.database.session import get_db
from app.models.usuarios import User
from app.schemas.rutina import (
    RutinaAssignClient,
    RutinaCreate,
    RutinaEjerciciosAssign,
    RutinaListResponse,
    RutinaResponse,
    RutinaUpdate,
)
from app.services.rutina_service import (
    EjercicioAlreadyAssignedError,
    EjercicioNotFoundError,
    RutinaNameExistsError,
    RutinaNotFoundError,
    RutinaService,
    UserNotFoundError,
)

STAFF_ROLES_NORMALIZED = {
    "superadministrador",
    "superadmin",
    "administrador",
    "admin",
    "entrenador",
    "trainer",
}


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    role = current_user.role
    candidates = {
        _normalize_role(role),
        _normalize_role(getattr(role, "name", None)),
    }
    is_super_admin = getattr(current_user, "super_admin_slot", None) == 1

    if is_super_admin or candidates & STAFF_ROLES_NORMALIZED:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para gestionar rutinas.",
    )


router = APIRouter(
    prefix="/rutinas",
    tags=["Rutinas"],
)


# RF-21: Consultar rutinas (listado general o filtrado por cliente)
@router.get("", response_model=RutinaListResponse)
def list_rutinas(
    search: str | None = Query(default=None, max_length=30),
    id_usuario: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista rutinas. Si el usuario es cliente, solo ve sus rutinas asignadas."""
    if _normalize_role(current_user.role) == "cliente":
        id_usuario = current_user.id_usuario

    items, total = RutinaService.list_rutinas(
        db,
        search=search,
        id_usuario=id_usuario,
        page=page,
        page_size=page_size,
    )
    return RutinaListResponse(
        items=[
            RutinaResponse(
                cod_rutina=item.cod_rutina,
                id_usuario=item.id_usuario,
                nombre=item.nombre,
                objetivo=item.objetivo,
                ejercicios=item.ejercicios or [],
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# RF-21: Consultar detalle de una rutina por su código
@router.get("/{cod_rutina}", response_model=RutinaResponse)
def get_rutina(
    cod_rutina: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene una rutina por su código."""
    try:
        rutina = RutinaService.get_rutina(db, cod_rutina)
    except RutinaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    if (
        _normalize_role(current_user.role) == "cliente"
        and rutina.id_usuario != current_user.id_usuario
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes consultar una rutina asignada a otro cliente.",
        )

    return RutinaResponse(
        cod_rutina=rutina.cod_rutina,
        id_usuario=rutina.id_usuario,
        nombre=rutina.nombre,
        objetivo=rutina.objetivo,
        ejercicios=rutina.ejercicios or [],
    )


# RF-020: Creación de rutina
@router.post(
    "",
    response_model=RutinaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
def create_rutina(
    data: RutinaCreate,
    db: Session = Depends(get_db),
):
    """Crea una nueva rutina."""
    try:
        rutina = RutinaService.create_rutina(db, data)
        return RutinaResponse(
            cod_rutina=rutina.cod_rutina,
            id_usuario=rutina.id_usuario,
            nombre=rutina.nombre,
            objetivo=rutina.objetivo,
            ejercicios=rutina.ejercicios or [],
        )
    except RutinaNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )


# RF-020.1: Asignar ejercicios a una rutina
@router.post(
    "/{cod_rutina}/ejercicios",
    response_model=RutinaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
def assign_ejercicios_to_rutina(
    cod_rutina: int,
    data: RutinaEjerciciosAssign,
    db: Session = Depends(get_db),
):
    """Asigna uno o varios ejercicios a una rutina."""
    try:
        rutina = RutinaService.assign_ejercicios(db, cod_rutina, data)
        return RutinaResponse(
            cod_rutina=rutina.cod_rutina,
            id_usuario=rutina.id_usuario,
            nombre=rutina.nombre,
            objetivo=rutina.objetivo,
            ejercicios=rutina.ejercicios or [],
        )
    except (RutinaNotFoundError, EjercicioNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except EjercicioAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


# RF-021: Editar rutina
@router.patch(
    "/{cod_rutina}",
    response_model=RutinaResponse,
    dependencies=[Depends(require_staff)],
)
def update_rutina(
    cod_rutina: int,
    data: RutinaUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente una rutina."""
    try:
        rutina = RutinaService.update_rutina(db, cod_rutina, data)
        return RutinaResponse(
            cod_rutina=rutina.cod_rutina,
            id_usuario=rutina.id_usuario,
            nombre=rutina.nombre,
            objetivo=rutina.objetivo,
            ejercicios=rutina.ejercicios or [],
        )
    except (RutinaNotFoundError, UserNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except RutinaNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


# RF-022 y RF-025: Asignar rutina a un cliente
@router.post(
    "/{cod_rutina}/asignar",
    response_model=RutinaResponse,
    dependencies=[Depends(require_staff)],
)
def assign_rutina_to_client(
    cod_rutina: int,
    data: RutinaAssignClient,
    db: Session = Depends(get_db),
):
    """Asigna una rutina existente a un cliente."""
    try:
        rutina = RutinaService.assign_to_client(db, cod_rutina, data.id_usuario)
        return RutinaResponse(
            cod_rutina=rutina.cod_rutina,
            id_usuario=rutina.id_usuario,
            nombre=rutina.nombre,
            objetivo=rutina.objetivo,
            ejercicios=rutina.ejercicios or [],
        )
    except (RutinaNotFoundError, UserNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )


# RF-024: Eliminar rutina
@router.delete(
    "/{cod_rutina}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_staff)],
)
def delete_rutina(
    cod_rutina: int,
    db: Session = Depends(get_db),
):
    """Elimina una rutina."""
    try:
        RutinaService.delete_rutina(db, cod_rutina)
    except RutinaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)