from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()


class NotificationService:
    async def notify_new_draft(self, *, draft_id: int, topic_title: str) -> None:
        message = f'New article awaiting approval: Draft #{draft_id} for topic "{topic_title}".'

        if all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from, settings.reviewer_notification_email]):
            await asyncio.to_thread(self._send_email, subject='New article awaiting approval', body=message)

    def _send_email(self, *, subject: str, body: str) -> None:
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = settings.smtp_from
        email['To'] = settings.reviewer_notification_email
        email.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(email)
