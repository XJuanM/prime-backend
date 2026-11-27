from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, get_db
from app.models.usuarios import User
from app.schemas.dietas import (
    DietaCreate,
    DietaOut,
    DietaUpdate,
)
from app.services import dietas

router = APIRouter(
    prefix="/dietas",
    tags=["dietas"]
)


# Crear una dieta para el usuario autenticado
@router.post(
    "/",
    response_model=DietaOut,
    status_code=status.HTTP_201_CREATED
)
def crear_dieta(
    data: DietaCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return dietas.crear(db, data, user.id_usuario)


# Listar las dietas del usuario autenticado (paginado)
@router.get(
    "/",
    response_model=list[DietaOut]
)
def listar_dietas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return dietas.listar(db, user.id_usuario, skip, limit)


# Obtener una dieta por su código
@router.get(
    "/{cod_dieta}",
    response_model=DietaOut
)
def obtener_dieta(
    cod_dieta: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    try:
        return dietas.obtener(db, cod_dieta, user.id_usuario)
    except dietas.DietaNoEncontrada:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Dieta no encontrada"
        )


# Actualizar parcialmente una dieta
@router.patch(
    "/{cod_dieta}",
    response_model=DietaOut
)
def actualizar_dieta(
    cod_dieta: int,
    data: DietaUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    try:
        return dietas.actualizar(db, cod_dieta, user.id_usuario, data)
    except dietas.DietaNoEncontrada:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Dieta no encontrada"
        )


# Eliminar una dieta
@router.delete(
    "/{cod_dieta}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_dieta(
    cod_dieta: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    try:
        dietas.eliminar(db, cod_dieta, user.id_usuario)
    except dietas.DietaNoEncontrada:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Dieta no encontrada"
        )