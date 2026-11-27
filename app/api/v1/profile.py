from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from app.models.usuarios import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile_service import ProfileService
from app.services.user_service import (
    UserNotFoundError,
    UserPermissionError,
    UserServiceError,
)


# Cualquier usuario autenticado, sin importar su rol, gestiona SU perfil.
router = APIRouter(
    prefix="/profile",
    tags=["Perfil personal"],
)


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Consultar mi perfil",
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ProfileService.get_profile(db, current_user)

    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.patch(
    "",
    response_model=ProfileResponse,
    summary="Actualizar mi perfil",
)
def update_my_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ProfileService.update_profile(db, current_user, data)

    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )

    except UserPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )

    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
