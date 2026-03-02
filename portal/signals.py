import logging
import socket
from urllib.parse import urlparse

from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from django.conf import settings
from django.urls import reverse

from .models import Post, AdResponse

logger = logging.getLogger(__name__)


def _is_celery_broker_available():
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    parsed = urlparse(broker_url)
    if parsed.scheme not in {"redis", "rediss"}:
        # For unknown schemes we don't block task sending.
        return True

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


@receiver(post_save, sender=User)
def add_user_to_common_group(sender, instance, created, **kwargs):
    if created:
        common_group, _ = Group.objects.get_or_create(name='common')
        instance.groups.add(common_group)


@receiver(m2m_changed, sender=Post.categories.through)
def notify_subscribers(sender, instance, action, **kwargs):
    """
    Сигнал для отправки асинхронных уведомлений при добавлении поста в категории
    """
    if action == "post_add":
        # Используем Celery для асинхронной отправки уведомлений.
        # Если брокер недоступен, не роняем запрос и пропускаем постановку в очередь.
        from .tasks import send_notification_to_subscribers
        category_ids = [cat.id for cat in instance.categories.all()]
        if category_ids:
            if not _is_celery_broker_available():
                logger.warning(
                    "Celery broker unavailable, notification task was not queued for post_id=%s",
                    instance.pk,
                )
                return
            try:
                send_notification_to_subscribers.apply_async(
                    args=(instance.pk, category_ids),
                    retry=False,
                )
            except Exception:
                logger.exception(
                    "Celery broker unavailable, notification task was not queued for post_id=%s",
                    instance.pk,
                )


@receiver(pre_save, sender=AdResponse)
def remember_previous_response_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_is_accepted = False
        return
    previous = AdResponse.objects.filter(pk=instance.pk).values('is_accepted').first()
    instance._old_is_accepted = previous['is_accepted'] if previous else False


@receiver(post_save, sender=AdResponse)
def notify_on_response_events(sender, instance, created, **kwargs):
    ad = instance.ad
    author = ad.author
    responder = instance.author

    base_url = 'http://127.0.0.1:8000'
    ad_link = f"{base_url}{ad.get_absolute_url()}"
    responses_link = f"{base_url}{reverse('pw_my_responses')}"

    if created and author.email:
        msg = EmailMultiAlternatives(
            subject=f'Perfect World: новый отклик на "{ad.title}"',
            body=(
                f'Здравствуйте, {author.username}!\n\n'
                f'Пользователь {responder.username} оставил отклик на ваше объявление.\n'
                f'Текст отклика:\n{instance.text}\n\n'
                f'Объявление: {ad_link}\n'
                f'Управление откликами: {responses_link}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[author.email],
        )
        msg.send(fail_silently=True)

    became_accepted = bool(instance.is_accepted) and not bool(getattr(instance, '_old_is_accepted', False))
    if became_accepted and responder.email:
        msg = EmailMultiAlternatives(
            subject=f'Perfect World: ваш отклик принят',
            body=(
                f'Здравствуйте, {responder.username}!\n\n'
                f'Ваш отклик на объявление "{ad.title}" был принят автором.\n'
                f'Ссылка на объявление: {ad_link}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[responder.email],
        )
        msg.send(fail_silently=True)

