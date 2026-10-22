import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import get_settings

logger = logging.getLogger("taskhub.notifications")


async def send_assignment_email(to_email: str, task_title: str, assigned_by: str) -> None:
    settings = get_settings()
    if not settings.mail_enabled:
        return
    title = " ".join(task_title.splitlines())
    try:
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = to_email
        message["Subject"] = f"You are assigned task: {title}"
        message.set_content(f'{assigned_by} has just assigned task "{title}" to you.')
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=settings.smtp_starttls,
        )
        logger.info("Sent assignment email to %s", to_email)
    except (aiosmtplib.SMTPException, OSError, ValueError):
        logger.exception("Failed to send assignment email to %s", to_email)
