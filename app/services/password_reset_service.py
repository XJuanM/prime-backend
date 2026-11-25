import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.password_reset_code import PasswordResetCode
from app.models.UserSession import UserSession
from app.repositories.user_repository import UserRepository

CODE_MINUTES = getattr(settings, "PASSWORD_RESET_CODE_MINUTES", 2)
MAX_ATTEMPTS = getattr(settings, "PASSWORD_RESET_MAX_ATTEMPTS", 5)
COOLDOWN_SECONDS = getattr(settings, "PASSWORD_RESET_COOLDOWN_SECONDS", 60)


class PasswordResetError(Exception):
    pass


class InvalidResetCodeError(PasswordResetError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_code(user_id: int, code: str) -> str:
    message = f"{user_id}:{code}".encode()
    return hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


class PasswordResetService:

    @staticmethod
    def request_reset(
        db: Session,
        email: str,
    ) -> tuple[str, str, str, int] | None:
        """Genera un código y devuelve los datos para enviarlo por correo.

        Devuelve None si el correo no existe, la cuenta está inactiva o se
        pidió un código hace menos de COOLDOWN_SECONDS. El endpoint responde
        igual en todos los casos para no revelar qué correos existen.
        """
        email = email.strip().lower()
        user = UserRepository.get_by_email(db, email)

        if user is None or not user.is_active:
            return None

        now = _now()

        last = db.scalar(
            select(PasswordResetCode)
            .where(PasswordResetCode.user_id == user.id)
            .order_by(PasswordResetCode.id.desc())
            .limit(1)
        )

        if last is not None and (
            now - last.created_at
        ).total_seconds() < COOLDOWN_SECONDS:
            return None

        code = f"{secrets.randbelow(1_000_000):06d}"

        try:
            # Solo puede haber un código vigente por usuario.
            db.execute(
                update(PasswordResetCode)
                .where(
                    PasswordResetCode.user_id == user.id,
                    PasswordResetCode.used_at.is_(None),
                )
                .values(used_at=now)
            )

            db.add(
                PasswordResetCode(
                    user_id=user.id,
                    code_hash=_hash_code(user.id, code),
                    expires_at=now + timedelta(minutes=CODE_MINUTES),
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        return user.email, user.first_name or "", code, CODE_MINUTES

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        code: str,
        new_password: str,
    ) -> None:
        email = email.strip().lower()
        user = UserRepository.get_by_email(db, email)

        if user is None or not user.is_active:
            raise InvalidResetCodeError("Código inválido o expirado.")

        now = _now()

        record = db.scalar(
            select(PasswordResetCode)
            .where(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.used_at.is_(None),
            )
            .order_by(PasswordResetCode.id.desc())
            .limit(1)
        )

        if record is None or now >= record.expires_at:
            raise InvalidResetCodeError("Código inválido o expirado.")

        try:
            expected = _hash_code(user.id, code)

            if not hmac.compare_digest(expected, record.code_hash):
                record.attempts += 1

                if record.attempts >= MAX_ATTEMPTS:
                    record.used_at = now

                db.commit()
                raise InvalidResetCodeError("Código inválido o expirado.")

            # Código correcto: se consume y se cambia la contraseña.
            record.used_at = now
            user.password_hash = hash_password(new_password)

            # Cierra todas las sesiones abiertas de la cuenta.
            db.execute(
                update(UserSession)
                .where(
                    UserSession.user_id == user.id,
                    UserSession.is_active.is_(True),
                )
                .values(is_active=False, revoked_at=now)
            )

            db.commit()

        except InvalidResetCodeError:
            raise
        except Exception:
            db.rollback()
            raise
