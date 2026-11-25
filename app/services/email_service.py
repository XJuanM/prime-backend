import logging
import smtplib
from email.message import EmailMessage
from html import escape

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_reset_code_email(
    to_email: str,
    first_name: str,
    code: str,
    minutes: int,
) -> None:
    """Envía el código de recuperación. Pensada para BackgroundTasks:
    nunca lanza excepciones hacia el endpoint."""

    name = first_name or "usuario"

    message = EmailMessage()
    message["Subject"] = "Código para recuperar tu contraseña"
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email

    message.set_content(
        f"Hola {name},\n\n"
        f"Tu código de recuperación es: {code}\n\n"
        f"Es válido por {minutes} minutos y solo se puede usar una vez.\n"
        "Si no solicitaste este cambio, ignora este mensaje.\n"
    )

    message.add_alternative(
        f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #222;">
    <p>Hola {escape(name)},</p>
    <p>Tu código de recuperación es:</p>
    <p style="font-size: 32px; font-weight: bold; letter-spacing: 6px;">
      {code}
    </p>
    <p>Es válido por <strong>{minutes} minutos</strong> y solo se puede
    usar una vez.</p>
    <p style="color: #777;">Si no solicitaste este cambio,
    ignora este mensaje.</p>
  </body>
</html>
""",
        subtype="html",
    )

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
        ) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception:
        logger.exception("No se pudo enviar el correo de recuperación.")
