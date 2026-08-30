import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


class NotificationService:
    async def send_telegram(self, bot_token: str, chat_id: str, message: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.telegram_api_base}/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
            )
            response.raise_for_status()
            return response.json()

    async def send_slack(self, webhook_url: str, message: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(webhook_url, json={"text": message})
            response.raise_for_status()
            return {"status": "sent"}

    async def send_discord(self, webhook_url: str, message: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(webhook_url, json={"content": message})
            response.raise_for_status()
            return {"status": "sent"}

    def send_email(self, to_email: str, subject: str, body: str) -> None:
        if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
            raise RuntimeError("SMTP settings are required for email notifications")
        message = EmailMessage()
        message["From"] = settings.notification_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
