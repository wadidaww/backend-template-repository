from __future__ import annotations

import structlog

from app.core.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="send_welcome_email", bind=True, max_retries=3)
def send_welcome_email(self, user_email: str, username: str) -> dict:
    """Send a welcome email to a newly registered user."""
    try:
        logger.info("sending_welcome_email", email=user_email, username=username)
        # In production, integrate with an email service (SendGrid, SES, etc.)
        return {"status": "sent", "email": user_email}
    except Exception as exc:
        logger.error("welcome_email_failed", email=user_email, error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="send_password_reset_email", bind=True, max_retries=3)
def send_password_reset_email(self, user_email: str, reset_token: str) -> dict:
    """Send a password reset email."""
    try:
        logger.info("sending_password_reset_email", email=user_email)
        # In production, integrate with an email service (SendGrid, SES, etc.)
        return {"status": "sent", "email": user_email}
    except Exception as exc:
        logger.error("password_reset_email_failed", email=user_email, error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc
