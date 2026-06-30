from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# The Celery app instance
# "ingestion" is just a name for this app, used internally by Celery
# broker = where tasks are queued (Redis db 1)
# backend = where task results are stored (Redis db 2)
celery_app = Celery(
    "ingestion",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.ingestion_tasks"],
    # include tells Celery which modules contain @celery_app.task functions
    # Without this, the worker process won't know these tasks exist
)

# Configuration for reliability and observability
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # task_track_started: mark task as STARTED when a worker picks it up,
    # not just PENDING -> SUCCESS. Useful for debugging stuck tasks.
    task_track_started=True,

    # task_acks_late: only acknowledge (remove from queue) after the task
    # actually completes. If a worker crashes mid-task, Redis redelivers
    # the task to another worker instead of losing it silently.
    task_acks_late=True,

    # worker_prefetch_multiplier=1: each worker takes one task at a time
    # Prevents one worker from hoarding 10 large PDF tasks while
    # other workers sit idle
    worker_prefetch_multiplier=1,
)