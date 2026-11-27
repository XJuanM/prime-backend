from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.schemas.ejercicio import (
    EjercicioCreate,
    EjercicioListResponse,
    EjercicioResponse,
    EjercicioUpdate,
)
from app.services.ejercicio_service import (
    EjercicioNameExistsError,
    EjercicioNotFoundError,
    EjercicioService,
)

router = APIRouter(
    prefix="/ejercicios",
    tags=["Ejercicios"],
)


@router.get("", response_model=EjercicioListResponse)
def list_ejercicios(
    search: str | None = Query(default=None, max_length=100),
    musculo_enfoque: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista los ejercicios con filtros opcionales y paginación."""
    items, total = EjercicioService.list_ejercicios(
        db,
        search=search,
        musculo_enfoque=musculo_enfoque,
        page=page,
        page_size=page_size,
    )
    return EjercicioListResponse(
        items=[EjercicioResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ejercicio_id}", response_model=EjercicioResponse)
def get_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene un ejercicio por su ID."""
    try:
        return EjercicioService.get_ejercicio(db, ejercicio_id)
    except EjercicioNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )


@router.post(
    "",
    response_model=EjercicioResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ejercicio(
    data: EjercicioCreate,
    db: Session = Depends(get_db),
):
    """Crea un nuevo ejercicio."""
    try:
        return EjercicioService.create_ejercicio(db, data)
    except EjercicioNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


@router.patch("/{ejercicio_id}", response_model=EjercicioResponse)
def update_ejercicio(
    ejercicio_id: int,
    data: EjercicioUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente un ejercicio."""
    try:
        return EjercicioService.update_ejercicio(db, ejercicio_id, data)
    except EjercicioNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except EjercicioNameExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )


@router.delete("/{ejercicio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
):
    """Elimina un ejercicio por su ID."""
    try:
        EjercicioService.delete_ejercicio(db, ejercicio_id)
    except EjercicioNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)