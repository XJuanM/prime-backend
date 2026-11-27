from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
)
from app.services.email_service import send_reset_code_email
from app.services.password_reset_service import (
    CODE_MINUTES,
    InvalidResetCodeError,
    PasswordResetService,
)

router = APIRouter(
    prefix="/auth",
    tags=["Recuperación de contraseña"],
)


@router.post("/forgot-password", response_model=MessageResponse, summary="Solicitar código de recuperación")
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Envía un código de 6 dígitos al correo, si la cuenta existe."""
    payload = PasswordResetService.request_reset(db, str(data.email))

    if payload is not None:
        background_tasks.add_task(send_reset_code_email, *payload)

    # Misma respuesta exista o no el correo.
    return MessageResponse(
        message=(
            "Si el correo está registrado, recibirás un código "
            f"válido por {CODE_MINUTES} minutos."
        )
    )


@router.post("/reset-password", response_model=MessageResponse, summary="Restablecer contraseña")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Cambia la contraseña usando el código recibido por correo."""
    try:
        PasswordResetService.reset_password(
            db=db,
            email=str(data.email),
            code=data.code,
            new_password=data.new_password,
        )
    except InvalidResetCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return MessageResponse(
        message="Contraseña actualizada. Inicia sesión nuevamente."
    )
