from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.domain.enums.muscle_group import MuscleGroup
from app.domain.enums.user_role import Roles
from app.infrastructure.database.session import get_db
from app.models.usuarios import User
from app.schemas.progress import (
    MonthlyProgressResponse,
    ProgressCreate,
    ProgressResponse,
    ProgressUpdate,
)
from app.services.progress_service import (
    ProgressAlreadyExistsError,
    ProgressIncompleteMonthError,
    ProgressNotFoundError,
    ProgressService,
    ProgressServiceError,
)

router = APIRouter(prefix="/progress", tags=["Progreso personal"])

# Pueden CONSULTAR el progreso de otros usuarios
STAFF_ROLES = (Roles.SUPER_ADMIN, Roles.ADMINISTRADOR, Roles.ENTRENADOR)
# Solo lectura: no pueden crear, editar ni eliminar progresos
READ_ONLY_ROLES = (Roles.SUPER_ADMIN, Roles.ADMINISTRADOR)

USER_ID_QUERY = Query(
    default=None,
    alias="usuario_id",
    description="ID del usuario. Obligatorio para el entrenador al registrar o editar.",
)


def resolve_read_user_id(usuario_id: int | None, current_user: User) -> int:
    """Un usuario ve lo suyo; el staff puede consultar a otros."""
    if usuario_id is None or usuario_id == current_user.id:
        return current_user.id

    if current_user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar el progreso de otro usuario.",
        )
    return usuario_id


def resolve_write_user_id(
    usuario_id: int | None, db: Session, current_user: User
) -> int:
    """Define a qué usuario pertenece el registro que se crea/edita/elimina.

    - Super admin / administrador: solo lectura.
    - Entrenador: debe indicar el usuario_id.
    - Usuario: solo puede modificar su propio progreso.
    """
    if current_user.role in READ_ONLY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el entrenador puede registrar o editar el progreso.",
        )

    if current_user.role == Roles.ENTRENADOR:
        if usuario_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Debes indicar el usuario_id del usuario al que pertenece el progreso.",
            )
        if db.get(User, usuario_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario indicado no existe.",
            )
        return usuario_id

    if usuario_id is not None and usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes modificar tu propio progreso.",
        )
    return current_user.id


@router.post("", response_model=ProgressResponse, status_code=status.HTTP_201_CREATED, summary="Registrar sesión de progreso")
def create_progress(
    data: ProgressCreate,
    usuario_id: int | None = USER_ID_QUERY,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = resolve_write_user_id(usuario_id, db, current_user)
    try:
        return ProgressService.create_record(db, target_id, data)
    except ProgressAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=list[ProgressResponse], summary="Listar sesiones de progreso")
def list_progress(
    usuario_id: int | None = USER_ID_QUERY,
    grupo_muscular: MuscleGroup | None = Query(default=None),
    anio: int | None = Query(default=None, ge=2000, le=2100),
    mes: int | None = Query(default=None, ge=1, le=12),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = resolve_read_user_id(usuario_id, current_user)
    return ProgressService.list_records(
        db, target_id, grupo_muscular, anio, mes, skip, limit
    )


@router.get("/metrics/monthly", response_model=MonthlyProgressResponse, summary="Calcular progreso mensual")
def monthly_metrics(
    grupo_muscular: MuscleGroup,
    anio: int = Query(ge=2000, le=2100),
    mes: int = Query(ge=1, le=12),
    usuario_id: int | None = USER_ID_QUERY,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = resolve_read_user_id(usuario_id, current_user)
    try:
        return ProgressService.monthly_progress(
            db, target_id, grupo_muscular, anio, mes
        )
    except ProgressIncompleteMonthError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.patch("/{progress_id}", response_model=ProgressResponse, summary="Actualizar sesión de progreso")
def update_progress(
    progress_id: int,
    data: ProgressUpdate,
    usuario_id: int | None = USER_ID_QUERY,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = resolve_write_user_id(usuario_id, db, current_user)
    try:
        return ProgressService.update_record(db, target_id, progress_id, data)
    except ProgressNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ProgressServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar sesión de progreso")
def delete_progress(
    progress_id: int,
    usuario_id: int | None = USER_ID_QUERY,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = resolve_write_user_id(usuario_id, db, current_user)
    try:
        ProgressService.delete_record(db, target_id, progress_id)
    except ProgressNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
