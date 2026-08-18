"""
Servicio de envío de correos electrónicos.
Usa SMTP genérico configurado por variables de entorno.
Soporta TLS (STARTTLS) y SSL directo.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings


def _build_mime_message(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> MIMEMultipart:
    """Construye el mensaje MIME multipart con versión HTML y texto plano."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email

    if body_text is None:
        # Conversión simple de HTML a texto plano
        body_text = (
            body_html
            .replace("<br>", "\n")
            .replace("</p>", "\n")
            .replace("<p>", "")
            .replace("&nbsp;", " ")
        )

    part_text = MIMEText(body_text, "plain", "utf-8")
    part_html = MIMEText(body_html, "html", "utf-8")
    msg.attach(part_text)
    msg.attach(part_html)
    return msg


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> None:
    """
    Envía un correo electrónico usando SMTP.
    Soporta TLS (STARTTLS) o SSL directo según configuración.

    :param to_email: destinatario
    :param subject: asunto
    :param body_html: cuerpo en HTML
    :param body_text: cuerpo en texto plano (opcional, se genera si no se envía)
    """
    msg = _build_mime_message(to_email, subject, body_html, body_text)

    if settings.SMTP_USE_SSL:
        # Conexión SSL directa
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT,
        ) as server:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
    else:
        # Conexión estándar con STARTTLS opcional
        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT,
        ) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Envía correo con enlace de recuperación de contraseña."""
    subject = "Recuperación de contraseña - SIPA"
    body_html = f"""
    <html>
        <body>
            <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Haz clic en el siguiente enlace para continuar:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>Este enlace es válido por {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos.</p>
            <p>Si no solicitaste este cambio, ignora este correo.</p>
        </body>
    </html>
    """
    send_email(to_email, subject, body_html)