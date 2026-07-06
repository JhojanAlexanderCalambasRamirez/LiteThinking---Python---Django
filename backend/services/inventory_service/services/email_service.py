from __future__ import annotations

import base64
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import config

logger = logging.getLogger(__name__)

_EMAIL_BACKEND = config("EMAIL_BACKEND", default="smtp")  # 'smtp' | 'sendgrid'


def send_inventory_email(
    recipient_email: str,
    empresa_nombre: str,
    pdf_bytes: bytes,
    filename: str = "inventario.pdf",
) -> bool:
    """
    Send inventory PDF by email.
    Supports SMTP (default) or SendGrid API backend.
    """
    if _EMAIL_BACKEND == "sendgrid":
        return _send_via_sendgrid(recipient_email, empresa_nombre, pdf_bytes, filename)
    return _send_via_smtp(recipient_email, empresa_nombre, pdf_bytes, filename)


def _send_via_smtp(
    recipient: str,
    empresa_nombre: str,
    pdf_bytes: bytes,
    filename: str,
) -> bool:
    host = config("SMTP_HOST", default="smtp.gmail.com")
    port = config("SMTP_PORT", default=587, cast=int)
    user = config("SMTP_USER")
    password = config("SMTP_PASSWORD")
    sender = config("EMAIL_FROM", default=user)

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = f"Inventario - {empresa_nombre}"

    body = MIMEText(
        f"Adjunto encontrará el reporte de inventario de {empresa_nombre}.\n\n"
        "Este correo fue generado automáticamente por LiteThinking.",
        "plain",
    )
    msg.attach(body)

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    try:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, recipient, msg.as_string())
        logger.info("Email sent to %s", recipient)
        return True
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", recipient, exc)
        return False


def _send_via_sendgrid(
    recipient: str,
    empresa_nombre: str,
    pdf_bytes: bytes,
    filename: str,
) -> bool:
    try:
        import sendgrid
        from sendgrid.helpers.mail import (
            Attachment,
            ContentId,
            Disposition,
            FileContent,
            FileName,
            FileType,
            Mail,
        )

        sg = sendgrid.SendGridAPIClient(api_key=config("SENDGRID_API_KEY"))
        mail = Mail(
            from_email=config("EMAIL_FROM"),
            to_emails=recipient,
            subject=f"Inventario - {empresa_nombre}",
            plain_text_content=(
                f"Adjunto encontrará el reporte de inventario de {empresa_nombre}.\n\n"
                "Este correo fue generado automáticamente por LiteThinking."
            ),
        )

        encoded = base64.b64encode(pdf_bytes).decode()
        mail.attachment = Attachment(
            FileContent(encoded),
            FileName(filename),
            FileType("application/pdf"),
            Disposition("attachment"),
        )

        response = sg.send(mail)
        logger.info("SendGrid response: %s", response.status_code)
        return response.status_code in (200, 202)
    except Exception as exc:
        logger.error("SendGrid error: %s", exc)
        return False
