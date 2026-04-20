import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendance_system.settings.development")

app = Celery("attendance_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "apps.authentication.tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=2, minute=0),
    },
    "mark-daily-absences": {
        "task": "apps.attendance.tasks.mark_daily_absences",
        "schedule": crontab(hour=23, minute=50),
    },
}
