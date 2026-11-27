from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.schemas.alimento import (
    AlimentoCreate,
    AlimentoListResponse,
    AlimentoResponse,
    AlimentoUpdate,
)
from app.services.alimento_service import (
    AlimentoNameExistsError,
    AlimentoNotFoundError,
    AlimentoService,
)

router = APIRouter(
    prefix="/alimentos",
    tags=["Alimentos"],
)


@router.get("", response_model=AlimentoListResponse, summary="Listar alimentos")
def list_alimentos(
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista los alimentos con búsqueda opcional y paginación."""
    items, total = AlimentoService.list_alimentos(
        db,
        search=search,
        page=page,
        page_size=page_size,
    )
    return AlimentoListResponse(
        items=[AlimentoResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{alimento_id}", response_model=AlimentoResponse, summary="Consultar alimento")
def get_alimento(
    alimento_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene un alimento por su ID."""
    try:
        return AlimentoService.get_alimento(db, alimento_id)
    except AlimentoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )


@router.post(
    "",
    response_model=AlimentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear alimento",
)
def create_alimento(
    data: AlimentoCreate,
    db: Session = Depends(get_db),
):
    """Crea un nuevo alimento."""
    try:
        return AlimentoService.create_alimento(db, data)
    except AlimentoNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


@router.patch("/{alimento_id}", response_model=AlimentoResponse, summary="Actualizar alimento")
def update_alimento(
    alimento_id: int,
    data: AlimentoUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente un alimento."""
    try:
        return AlimentoService.update_alimento(db, alimento_id, data)
    except AlimentoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except AlimentoNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


@router.delete("/{alimento_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar alimento")
def delete_alimento(
    alimento_id: int,
    db: Session = Depends(get_db),
):
    """Elimina un alimento por su ID."""
    try:
        AlimentoService.delete_alimento(db, alimento_id)
    except AlimentoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)