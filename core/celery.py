import os

from celery import Celery
# set the default Django settings module for the 'celery' program.
from django.apps import apps

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("beautiland")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# app.conf.beat_schedule = {
#     'update_booking_machin_data': {
#         'task': 'apps.machines.tasks.session_handler',
#         'schedule': crontab("*"),
#     },
# }