import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lunch_voter.settings')

app = Celery('lunch_voter')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

