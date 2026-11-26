from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()

    celery = Celery(
        "backend_template",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        broker_connection_retry_on_startup=True,
        task_always_eager=settings.is_testing,
    )
    # Each module keeps its tasks in app/modules/<name>/tasks.py
    celery.autodiscover_tasks(["app.modules.notifications"])
    return celery


celery_app = create_celery_app()
