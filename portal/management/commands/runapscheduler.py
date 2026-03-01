import logging
from datetime import timedelta

from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from portal.models import Post

logger = logging.getLogger(__name__)


def send_weekly_digest():
    """Отправляет еженедельный дайджест подписчикам с новыми статьями"""
    # Получаем всех пользователей
    users = User.objects.filter(subscribed_categories__isnull=False).distinct()
    
    # Время неделю назад
    one_week_ago = timezone.now() - timedelta(days=7)
    
    for user in users:
        # Получаем категории, на которые подписан пользователь
        subscribed_categories = user.subscribed_categories.all()
        
        # Получаем посты из этих категорий за последнюю неделю
        posts = Post.objects.filter(
            categories__in=subscribed_categories,
            created_at__gte=one_week_ago
        ).distinct().order_by('-created_at')
        
        # Если есть новые посты, отправляем дайджест
        if posts.exists() and user.email:
            html_content = render_to_string(
                'portal/email/weekly_digest.html',
                {
                    'user': user,
                    'posts': posts,
                    'categories': subscribed_categories,
                }
            )
            
            msg = EmailMultiAlternatives(
                subject=f'Еженедельный дайджест новостей от News Portal',
                body=f'Здравствуйте, {user.username}! Вот новые статьи за неделю в ваших любимых разделах.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"Еженедельный дайджест отправлен пользователю {user.email}")


def delete_old_job_executions(max_age=604_800):
    """Удаляет старые записи о выполнении задач старше max_age секунд"""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Запускает планировщик периодических задач (APScheduler)"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        if getattr(settings, "APSCHEDULER_ENABLE_WEEKLY_DIGEST", False):
            scheduler.add_job(
                send_weekly_digest,
                trigger=CronTrigger(day_of_week="mon", hour="08", minute="00"),
                id="send_weekly_digest",
                max_instances=1,
                replace_existing=True,
            )
            logger.info(
                "Добавлена задача 'send_weekly_digest' "
                "(еженедельно по понедельникам в 08:00)"
            )
        else:
            logger.info(
                "Задача 'send_weekly_digest' через APScheduler отключена "
                "(используется Celery Beat)."
            )

        # Добавляем задачу удаления старых логов выполнения (каждый понедельник в 01:00)
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(day_of_week="mon", hour="01", minute="00"),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Добавлена задача 'delete_old_job_executions' (еженедельно по понедельникам)")

        try:
            logger.info("Запуск планировщика...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Остановка планировщика...")
            scheduler.shutdown()
            logger.info("Планировщик успешно остановлен!")
