import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news.settings')

app = Celery('news')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Конфигурация Celery Beat для периодических задач
app.conf.beat_schedule = {
    'send_weekly_digest': {
        'task': 'portal.tasks.send_weekly_digest',
        'schedule': crontab(day_of_week='mon', hour=8, minute=0),
    },
}

# Общие настройки Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
)
