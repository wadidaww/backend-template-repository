"""Email tasks. Delivery is still a stub; a provider interface arrives in step 6."""

from __future__ import annotations

from typing import Any

import structlog

from app.core.celery_app import celery_app
from app.utils.text import mask_string

logger = structlog.get_logger(__name__)


def _masked(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{mask_string(local, visible_start=1, visible_end=0)}@{domain}"


@celery_app.task(name="send_welcome_email", bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def send_welcome_email(self: Any, user_email: str, username: str) -> dict[str, str]:
    """Send a welcome email to a newly registered user."""
    try:
        logger.info("sending_welcome_email", email=_masked(user_email))
        return {"status": "sent", "email": user_email}
    except Exception as exc:
        logger.error("welcome_email_failed", email=_masked(user_email), error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="send_password_reset_email", bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def send_password_reset_email(
    self: Any, user_email: str, reset_token: str
) -> dict[str, str]:
    """Send a password reset email."""
    try:
        logger.info("sending_password_reset_email", email=_masked(user_email))
        return {"status": "sent", "email": user_email}
    except Exception as exc:
        logger.error(
            "password_reset_email_failed", email=_masked(user_email), error=str(exc)
        )
        raise self.retry(exc=exc, countdown=60) from exc
