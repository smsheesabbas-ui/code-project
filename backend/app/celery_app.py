from celery import Celery
from .config import settings

# Create Celery app
celery_app = Celery(
    "cashflow_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Configure periodic tasks
celery_app.conf.beat_schedule = {
    "check-alerts": {
        "task": "app.tasks.check_alerts",
        "schedule": 3600.0,  # Every hour
    },
    "send-weekly-summaries": {
        "task": "app.tasks.send_weekly_summaries", 
        "schedule": 604800.0,  # Every week (7 days)
        "options": {"queue": "periodic"},
    },
}

celery_app.conf.timezone = "UTC"
