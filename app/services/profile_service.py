from sqlalchemy.orm import Session

from app.domain.enums.user_role import Roles
from app.models.usuarios import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.user_service import (
    UserNotFoundError,
    UserPermissionError,
    UserService,
)


class ProfileService:

    @staticmethod
    def get_profile(db: Session, current_user: User) -> ProfileResponse:
        user = UserService.get_user(db, current_user.id)

        return ProfileResponse.model_validate(user)

    @staticmethod
    def update_profile(
        db: Session,
        current_user: User,
        data: ProfileUpdate,
    ) -> ProfileResponse:

        # Siempre se edita al usuario autenticado: no se recibe ningún id.
        user = UserService.get_user(db, current_user.id)

        # exclude_unset: solo cambia lo que el usuario envió explícitamente.
        changes = data.model_dump(exclude_unset=True)
        client_changes = changes.pop("client_profile", None)

        # Validar permisos ANTES de modificar nada.
        if client_changes:
            if user.role != Roles.CLIENTE:
                raise UserPermissionError(
                    "Solo los clientes tienen perfil de cliente."
                )

            if user.client_profile is None:
                raise UserNotFoundError(
                    "No se encontró tu perfil de cliente."
                )

            for field, value in client_changes.items():
                setattr(user.client_profile, field, value)

        for field, value in changes.items():
            setattr(user, field, value)

        try:
            db.commit()
            db.refresh(user)

        except Exception:
            db.rollback()
            raise

        return ProfileResponse.model_validate(user)
