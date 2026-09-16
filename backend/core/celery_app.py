import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # points to your settings

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Re-confirm every posting nightly and drop the ones that have gone away, so a
# match is never older than this interval. Celery's own beat is enough here —
# django_celery_beat would only add a DB-editable schedule we do not need yet.
# Runs with: celery -A core.celery_app beat -l info
app.conf.beat_schedule = {
    "refresh-jobs-nightly": {
        "task": "apps.jobs.tasks.refresh_jobs",
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {"limit": 100},
    },
}
