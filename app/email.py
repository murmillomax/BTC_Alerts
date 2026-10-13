import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)


def send_verification_email(
    recipient: str,
    verification_code: str
):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USERNAME o SMTP_PASSWORD no están configurados"
        )

    message = EmailMessage()

    message["Subject"] = "BTC Alerts - Código de verificación"
    message["From"] = SMTP_FROM
    message["To"] = recipient

    message.set_content(
        f"""Hola,

Gracias por registrarte en BTC Alerts.

Tu código de verificación es:

{verification_code}

Este código tiene una validez de 15 minutos.

Una vez verificado tu correo electrónico, se activará tu período de prueba de 3 meses.

Si no realizaste este registro, puedes ignorar este mensaje.

BTC Alerts
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

def _send_auth_code_email(
    recipient: str,
    code: str,
    purpose: str
):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USERNAME o SMTP_PASSWORD no están configurados"
        )

    if purpose == "login":
        subject = "BTC Alerts - Código de acceso"
        action = "iniciar sesión"
    elif purpose == "reset":
        subject = "BTC Alerts - Recuperación de contraseña"
        action = "restablecer tu contraseña"
    else:
        raise ValueError("Tipo de correo no válido")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = recipient

    message.set_content(
        f"""Hola,

Recibimos una solicitud para {action} en BTC Alerts.

Tu código de seguridad es:

{code}

Este código vence en 15 minutos y solo debe utilizarse
para la operación que solicitaste.

Si no realizaste esta solicitud, ignora este mensaje.
No compartas el código con nadie.

BTC Alerts
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


def send_login_code_email(recipient: str, code: str):
    _send_auth_code_email(recipient, code, "login")


def send_password_reset_email(recipient: str, code: str):
    _send_auth_code_email(recipient, code, "reset")
