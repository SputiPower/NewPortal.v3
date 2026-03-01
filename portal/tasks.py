from celery import shared_task
import logging
import traceback
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from datetime import timedelta

from .models import Post


@shared_task
def send_notification_to_subscribers(post_id, category_ids=None):
    """
    Асинхронная задача для отправки уведомлений подписчикам о новом посте
    """
    logger = logging.getLogger('portal.tasks')
    try:
        post = Post.objects.get(pk=post_id)

        # Если переданы конкретные категории, используем их, иначе все категории поста
        if category_ids:
            categories = post.categories.filter(id__in=category_ids)
        else:
            categories = post.categories.all()

        # Собираем уникальных подписчиков из всех категорий
        subscribers = set()
        for category in categories:
            for user in category.subscribers.all():
                subscribers.add(user)

        # Отправляем письма каждому подписчику
        for user in subscribers:
            if user.email:
                send_post_notification_email.delay(post_id, user.id)

    except Exception as e:
        logger.exception('Error in send_notification_to_subscribers for post_id=%s: %s', post_id, e)
        with open('celery_tasks_error.log', 'a', encoding='utf-8') as f:
            f.write('send_notification_to_subscribers ERROR for post_id=%s\n' % post_id)
            f.write(traceback.format_exc())
            f.write('\n')


@shared_task
def send_post_notification_email(post_id, user_id):
    """
    Асинхронная задача для отправки письма об одном посте конкретному пользователю
    """
    logger = logging.getLogger('portal.tasks')
    try:
        post = Post.objects.get(pk=post_id)
        user = User.objects.get(pk=user_id)

        # Генерируем HTML из шаблона
        html_content = render_to_string(
            'news/email_notification.html',
            {
                'user': user,
                'post': post,
                'link': f"http://127.0.0.1:8000{post.get_absolute_url()}" if hasattr(post, "get_absolute_url") else "#",
            }
        )

        # Отправляем письмо
        msg = EmailMultiAlternatives(
            subject=f'Новая статья: {post.title}',
            body=f'Здравствуй, {user.username}. Новая статья в твоём любимом разделе!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    except Exception as e:
        logger.exception('Error in send_post_notification_email post_id=%s user_id=%s: %s', post_id, user_id, e)
        with open('celery_tasks_error.log', 'a', encoding='utf-8') as f:
            f.write('send_post_notification_email ERROR for post_id=%s user_id=%s\n' % (post_id, user_id))
            f.write(traceback.format_exc())
            f.write('\n')


@shared_task
def send_weekly_digest():
    """
    Асинхронная задача для отправки еженедельного дайджеста с новыми статьями.
    Запускается каждый понедельник в 8:00 утра.
    """
    logger = logging.getLogger('portal.tasks')
    try:
        # Получаем пользователей, подписанных на категории
        users = User.objects.filter(subscribed_categories__isnull=False).distinct()

        # Время неделю назад
        one_week_ago = timezone.now() - timedelta(days=7)

        for user in users:
            if user.email:
                send_digest_email.delay(user.id, one_week_ago.isoformat())
    except Exception as e:
        logger.exception('Error in send_weekly_digest: %s', e)
        with open('celery_tasks_error.log', 'a', encoding='utf-8') as f:
            f.write('send_weekly_digest ERROR\n')
            f.write(traceback.format_exc())
            f.write('\n')


@shared_task
def send_digest_email(user_id, one_week_ago_iso):
    """
    Асинхронная задача для отправки дайджеста конкретному пользователю
    """
    logger = logging.getLogger('portal.tasks')
    try:
        user = User.objects.get(pk=user_id)
        one_week_ago = timezone.datetime.fromisoformat(one_week_ago_iso)

        # Получаем категории, на которые подписан пользователь
        subscribed_categories = user.subscribed_categories.all()

        # Получаем посты из этих категорий за последнюю неделю
        posts = Post.objects.filter(
            categories__in=subscribed_categories,
            created_at__gte=one_week_ago
        ).distinct().order_by('-created_at')

        # Если есть новые посты, отправляем дайджест
        if posts.exists():
            html_content = render_to_string(
                'news/email/weekly_digest.html',
                {
                    'user': user,
                    'posts': posts,
                    'categories': subscribed_categories,
                }
            )

            msg = EmailMultiAlternatives(
                subject='Еженедельный дайджест News Portal',
                body=f'Здравствуй, {user.username}! Вот новые статьи за неделю в ваших любимых разделах.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
    except Exception as e:
        logger.exception('Error in send_digest_email user_id=%s: %s', user_id, e)
        with open('celery_tasks_error.log', 'a', encoding='utf-8') as f:
            f.write('send_digest_email ERROR for user_id=%s\n' % user_id)
            f.write(traceback.format_exc())
            f.write('\n')
