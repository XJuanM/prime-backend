"""Servicio de autenticación.

Responsabilidades:
- Buscar al usuario por correo.
- Bloquear temporalmente la cuenta tras demasiados intentos fallidos.
- Verificar su contraseña.
- Comprobar que esté activo.
- Generar un JWT.
- Registrar la sesión en MySQL.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.models.usuarios import User
from app.models.UserSession import UserSession


class AuthenticationError(Exception):
    """Error cuando las credenciales no son válidas."""


class AccountLockedError(Exception):
    """La cuenta está bloqueada temporalmente por intentos fallidos."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Cuenta bloqueada temporalmente.")


def authenticate_user(
    db: Session,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[str, int]:
    """
    Autentica al usuario y registra una sesión.

    Retorna:
        (access_token, expires_in)

    Lanza:
        AuthenticationError: credenciales inválidas o usuario inactivo.
        AccountLockedError: cuenta bloqueada por intentos fallidos.
    """

    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    # 1. Buscar al usuario por correo.
    #    with_for_update bloquea la fila (InnoDB) para que peticiones
    #    simultáneas no pierdan incrementos del contador.
    user = db.scalar(
        select(User).where(User.email == email.lower()).with_for_update()
    )

    # El mismo mensaje en todos los casos evita revelar si el correo existe.
    if user is None:
        raise AuthenticationError(
            "Correo electrónico o contraseña incorrectos."
        )

    # 2. ¿Cuenta bloqueada? Ni siquiera se verifica la contraseña.
    if user.locked_until and user.locked_until > now_naive:
        remaining = int((user.locked_until - now_naive).total_seconds()) + 1
        db.rollback()  # libera el lock de la fila
        raise AccountLockedError(retry_after_seconds=remaining)

    # 3. Verificar la contraseña.
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = now_naive + timedelta(
                minutes=settings.LOCKOUT_MINUTES
            )
            # El contador arranca de cero tras el bloqueo.
            user.failed_login_attempts = 0

        db.commit()  # persistir ANTES de lanzar la excepción
        raise AuthenticationError(
            "Correo electrónico o contraseña incorrectos."
        )

    # 4. Comprobar que el usuario esté activo.
    if not user.is_active:
        db.rollback()
        raise AuthenticationError(
            "Correo electrónico o contraseña incorrectos."
        )

    # 5. Login correcto: limpiar contador y bloqueo.
    #    Se confirma junto con la sesión en el commit del paso 9.
    user.failed_login_attempts = 0
    user.locked_until = None

    # 6. Fechas de expiración en UTC.
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expires_at = now + timedelta(seconds=expires_in)

    # 7. Identificador único para esta sesión.
    jti = str(uuid4())

    # 8. Contenido y firma del JWT.
    payload = {
        "sub": str(user.id),
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }

    access_token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    # 9. Registrar la sesión en MySQL.
    session_record = UserSession(
        user_id=user.id,
        jti=jti,
        last_activity_at=now_naive,
        expires_at=expires_at.replace(tzinfo=None),
        is_active=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    try:
        db.add(session_record)
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    # 10. Entregar el token y su duración.
    return access_token, expires_in
