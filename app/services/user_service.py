from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.enums.user_role import Roles
from app.models.usuarios import User
from app.models.UserSession import UserSession
from app.models.client_profile import ClientProfile
from app.models.trainer_profile import TrainerProfile
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserServiceError(Exception):
    pass


class UserNotFoundError(UserServiceError):
    pass


class UserAlreadyExistsError(UserServiceError):
    pass


class UserPermissionError(UserServiceError):
    pass


class UserHasRelatedDataError(UserServiceError):
    pass


class UserService:

    # ------------------------------------------------------------------
    # Reglas de permisos
    # (SUPUESTOS: ajústalas si tus reglas de negocio son otras)
    # ------------------------------------------------------------------
    @staticmethod
    def ensure_can_create(current_user: User, target_role: Roles) -> None:
        """Quién puede crear qué rol."""
        if target_role == Roles.SUPER_ADMIN:
            raise UserPermissionError(
                "No se puede crear otro SUPER_ADMIN."
            )

        if current_user.role == Roles.SUPER_ADMIN:
            return

        if current_user.role == Roles.ENTRENADOR:
            if target_role != Roles.CLIENTE:
                raise UserPermissionError(
                    "El entrenador solo puede crear clientes."
                )
            return

        raise UserPermissionError("No tienes permisos para crear usuarios.")

    @staticmethod
    def _can_view(current_user: User, target: User) -> bool:
        """Super admin y administrador ven a todos; el entrenador solo clientes."""
        if current_user.role in (Roles.SUPER_ADMIN, Roles.ADMINISTRADOR):
            return True

        if current_user.role == Roles.ENTRENADOR:
            return target.role == Roles.CLIENTE

        return False

    # ------------------------------------------------------------------
    # Crear
    # ------------------------------------------------------------------
    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:

        email = str(data.email).strip().lower()

        if UserRepository.get_by_email(db, email):
            raise UserAlreadyExistsError(
                "Ya existe un usuario registrado con ese correo."
            )

        user = User(
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            email=email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=True,
        )

        try:
            db.add(user)
            db.flush()

            if data.role == Roles.CLIENTE:
                profile_data = data.client_profile.model_dump()
                db.add(
                    ClientProfile(
                        user_id=user.id,
                        **profile_data,
                    )
                )

            elif data.role in (
                Roles.ADMINISTRADOR,
                Roles.ENTRENADOR,
            ):
                profile_data = data.trainer_profile.model_dump()
                db.add(
                    TrainerProfile(
                        user_id=user.id,
                        **profile_data,
                    )
                )

            db.commit()
            db.refresh(user)

            return user

        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyExistsError(
                "No fue posible registrar el usuario. "
                "Verifica que el correo no esté duplicado."
            ) from exc

        except Exception:
            db.rollback()
            raise

    # ------------------------------------------------------------------
    # Consultar
    # ------------------------------------------------------------------
    @staticmethod
    def get_user(db: Session, user_id: int) -> User:

        user = UserRepository.get_by_id(db, user_id)

        if user is None:
            raise UserNotFoundError(
                "No se encontró el usuario solicitado."
            )

        return user

    @staticmethod
    def get_visible_user(
        db: Session, user_id: int, current_user: User
    ) -> User:
        user = UserService.get_user(db, user_id)

        # Si no puede verlo, se responde como "no encontrado"
        # para no revelar que el usuario existe.
        if not UserService._can_view(current_user, user):
            raise UserNotFoundError(
                "No se encontró el usuario solicitado."
            )

        return user

    @staticmethod
    def list_users(
        db: Session,
        role: Roles | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
        current_user: User | None = None,
    ) -> list[User]:

        # El entrenador solo ve clientes.
        if current_user is not None and current_user.role == Roles.ENTRENADOR:
            if role is not None and role != Roles.CLIENTE:
                return []
            role = Roles.CLIENTE

        return UserRepository.list_users(
            db=db,
            role=role,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Actualizar
    # ------------------------------------------------------------------
    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        data: UserUpdate,
    ) -> User:

        user = UserService.get_user(db, user_id)

        if user.role == Roles.SUPER_ADMIN:
            raise UserServiceError(
                "No se puede modificar el SUPER_ADMIN desde este módulo."
            )

        changes = data.model_dump(exclude_unset=True)

        if "email" in changes and changes["email"] is not None:
            changes["email"] = str(changes["email"]).strip().lower()

            existing = UserRepository.get_by_email(
                db, changes["email"]
            )

            if existing is not None and existing.id != user.id:
                raise UserAlreadyExistsError(
                    "Ese correo electrónico ya está registrado."
                )

        for field, value in changes.items():
            if isinstance(value, str):
                value = value.strip()

            setattr(user, field, value)

        try:
            db.commit()
            db.refresh(user)
            return user

        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyExistsError(
                "No fue posible actualizar el usuario. "
                "Verifica que el correo no esté duplicado."
            ) from exc

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def change_status(
        db: Session,
        user_id: int,
        is_active: bool,
        current_user_id: int,
    ) -> User:

        user = UserService.get_user(db, user_id)

        if user.role == Roles.SUPER_ADMIN:
            raise UserServiceError(
                "No se puede cambiar el estado del SUPER_ADMIN."
            )

        if user.id == current_user_id and not is_active:
            raise UserServiceError(
                "No puedes desactivar tu propia cuenta."
            )

        user.is_active = is_active

        try:
            if not is_active:
                now = datetime.now(timezone.utc).replace(tzinfo=None)

                db.execute(
                    update(UserSession)
                    .where(
                        UserSession.user_id == user.id,
                        UserSession.is_active.is_(True),
                    )
                    .values(
                        is_active=False,
                        revoked_at=now,
                    )
                )

            db.commit()
            db.refresh(user)
            return user

        except Exception:
            db.rollback()
            raise

    # ------------------------------------------------------------------
    # Eliminar
    # ------------------------------------------------------------------
    @staticmethod
    def delete_user(
        db: Session,
        user_id: int,
        current_user: User,
    ) -> None:

        user = UserService.get_user(db, user_id)

        if user.id == current_user.id:
            raise UserServiceError("No puedes eliminar tu propia cuenta.")

        if user.role == Roles.SUPER_ADMIN:
            raise UserPermissionError("No se puede eliminar el SUPER_ADMIN.")

        # Un administrador no puede eliminar a otro administrador.
        if (
            current_user.role == Roles.ADMINISTRADOR
            and user.role == Roles.ADMINISTRADOR
        ):
            raise UserPermissionError(
                "Un administrador no puede eliminar a otro administrador."
            )

        try:
            db.delete(user)
            db.commit()

        except IntegrityError as exc:
            db.rollback()
            raise UserHasRelatedDataError(
                "No se puede eliminar el usuario porque tiene información "
                "asociada (rutinas, membresías, etc.). Desactívalo en su lugar."
            ) from exc

        except Exception:
            db.rollback()
            raise
