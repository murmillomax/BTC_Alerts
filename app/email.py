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