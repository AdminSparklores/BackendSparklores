import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sparklore.settings")

app = Celery("sparklore")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

import api.orders.tasks 

app.conf.beat_schedule = {
    "update-orders-tracking-every-10-minutes": {
        "task": "api.orders.tasks.update_order_status_from_tracking",
        "schedule": crontab(minute="*/10"),   
    },
}
