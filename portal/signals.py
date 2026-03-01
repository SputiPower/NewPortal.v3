from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import Post

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
        # Используем Celery для асинхронной отправки уведомлений
        from .tasks import send_notification_to_subscribers
        category_ids = [cat.id for cat in instance.categories.all()]
        if category_ids:
            send_notification_to_subscribers.delay(instance.pk, category_ids)

