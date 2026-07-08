from __future__ import annotations

import base64
import logging
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import UndefinedValueError, config

logger = logging.getLogger(__name__)

_EMAIL_BACKEND = config("EMAIL_BACKEND", default="log")  # 'smtp' | 'sendgrid' | 'log'


def send_inventory_email(
    recipient_email: str,
    empresa_nombre: str,
    pdf_bytes: bytes,
    filename: str = "inventario.pdf",
    items_count: int = 0,
) -> bool:
    if _EMAIL_BACKEND == "sendgrid":
        return _send_via_sendgrid(recipient_email, empresa_nombre, pdf_bytes, filename, items_count)
    if _EMAIL_BACKEND == "log":
        return _send_via_log(recipient_email, empresa_nombre, filename, items_count)
    return _send_via_smtp(recipient_email, empresa_nombre, pdf_bytes, filename, items_count)


_MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _fecha_es() -> tuple[str, str]:
    now = datetime.now()
    corta = now.strftime("%d/%m/%Y")
    larga = f"{now.day} de {_MESES[now.month]} de {now.year}"
    return corta, larga


def _subject(empresa_nombre: str) -> str:
    corta, _ = _fecha_es()
    return f"Reporte de Inventario - {empresa_nombre} | {corta}"


def _body_plain(empresa_nombre: str, items_count: int) -> str:
    _, fecha = _fecha_es()
    return (
        f"Estimado usuario,\n\n"
        f"Se adjunta el reporte de inventario correspondiente a {empresa_nombre},\n"
        f"generado el {fecha} con un total de {items_count} producto(s) registrado(s).\n\n"
        f"El reporte en formato PDF se encuentra adjunto a este correo.\n\n"
        f"---\n"
        f"Este mensaje fue generado automaticamente por LiteThinking.\n"
        f"Por favor no responda a este correo."
    )


def _body_html(empresa_nombre: str, items_count: int) -> str:
    _, fecha = _fecha_es()
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="background:#1e3a5f;padding:24px 32px;">
            <p style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:.5px;">LiteThinking</p>
            <p style="margin:4px 0 0;color:#93c5fd;font-size:12px;">Sistema de Gestion de Inventario</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px;">
            <h2 style="margin:0 0 8px;color:#111827;font-size:18px;">Reporte de Inventario</h2>
            <p style="margin:0 0 24px;color:#6b7280;font-size:14px;">
              Se adjunta el reporte solicitado con el detalle de productos en inventario.
            </p>

            <!-- Info table -->
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:28px;">
              <tr style="background:#f9fafb;">
                <td style="padding:10px 16px;font-size:13px;font-weight:600;color:#374151;width:40%;border-bottom:1px solid #e5e7eb;">Empresa</td>
                <td style="padding:10px 16px;font-size:13px;color:#111827;border-bottom:1px solid #e5e7eb;">{empresa_nombre}</td>
              </tr>
              <tr>
                <td style="padding:10px 16px;font-size:13px;font-weight:600;color:#374151;background:#f9fafb;border-bottom:1px solid #e5e7eb;">Fecha</td>
                <td style="padding:10px 16px;font-size:13px;color:#111827;border-bottom:1px solid #e5e7eb;">{fecha}</td>
              </tr>
              <tr style="background:#f9fafb;">
                <td style="padding:10px 16px;font-size:13px;font-weight:600;color:#374151;">Productos</td>
                <td style="padding:10px 16px;font-size:13px;color:#111827;">
                  <span style="background:#dbeafe;color:#1d4ed8;padding:2px 10px;border-radius:999px;font-weight:600;">{items_count} registros</span>
                </td>
              </tr>
            </table>

            <p style="margin:0;color:#6b7280;font-size:13px;">
              El reporte completo en formato PDF se encuentra adjunto a este correo.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:16px 32px;">
            <p style="margin:0;color:#9ca3af;font-size:11px;text-align:center;">
              Este mensaje fue generado automaticamente por LiteThinking &mdash; por favor no responda a este correo.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _send_via_log(recipient: str, empresa_nombre: str, filename: str, items_count: int) -> bool:
    logger.info(
        "[LOG BACKEND] Email NOT sent. Would have sent '%s' with attachment '%s' (%d items) to '%s'.",
        _subject(empresa_nombre),
        filename,
        items_count,
        recipient,
    )
    return True


def _send_via_smtp(
    recipient: str,
    empresa_nombre: str,
    pdf_bytes: bytes,
    filename: str,
    items_count: int,
) -> bool:
    try:
        host = config("SMTP_HOST", default="smtp.gmail.com")
        port = config("SMTP_PORT", default=587, cast=int)
        user = config("SMTP_USER")
        password = config("SMTP_PASSWORD")
        sender = config("EMAIL_FROM", default=user)
    except UndefinedValueError as exc:
        logger.error("SMTP not configured: %s. Set SMTP_USER and SMTP_PASSWORD in .env.", exc)
        return False

    outer = MIMEMultipart("mixed")
    outer["From"] = sender
    outer["To"] = recipient
    outer["Subject"] = _subject(empresa_nombre)

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(_body_plain(empresa_nombre, items_count), "plain", "utf-8"))
    alt.attach(MIMEText(_body_html(empresa_nombre, items_count), "html", "utf-8"))
    outer.attach(alt)

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    outer.attach(attachment)

    try:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, recipient, outer.as_string())
        logger.info("Email sent to %s (%d items)", recipient, items_count)
        return True
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", recipient, exc)
        return False


def _send_via_sendgrid(
    recipient: str,
    empresa_nombre: str,
    pdf_bytes: bytes,
    filename: str,
    items_count: int,
) -> bool:
    try:
        import sendgrid
        from sendgrid.helpers.mail import (
            Attachment,
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
            subject=_subject(empresa_nombre),
            plain_text_content=_body_plain(empresa_nombre, items_count),
            html_content=_body_html(empresa_nombre, items_count),
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
