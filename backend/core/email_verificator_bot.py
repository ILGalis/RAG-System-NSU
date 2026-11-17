import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

logger = logging.getLogger(__name__)
#прописаны в .env
#менять соответственно там 
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

#async используется чтобы сервер не ждал действия пользователя
async def send_verification_email(to_email: str, code: str) -> bool:
    #Отправляет код подтверждения. Возвращает False при ошибке, не выбрасывает исключение
     #   чтобы не ломать роутеры и общий формат ошибок
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials не заданы. Письмо не отправлено. Код: %s", code)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Подтверждение почты"
    msg["From"] = f"RAG System Registration <{SMTP_FROM}>"
    msg["To"] = to_email
    #севчику братику html немножко
    html = f"""
    <p>Здравствуйте!</p>
    <p>Ваш код подтверждения: <strong>{code}</strong></p>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
        )
        logger.info("Письмо с кодом отправлено на %s", to_email)
        return True
    except Exception:
        logger.exception("Не удалось отправить письмо на %s", to_email)
        return False