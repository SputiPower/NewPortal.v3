from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from .models import Post

@receiver(post_save, sender=User)
def add_user_to_common_group(sender, instance, created, **kwargs):
    if created:
        common_group, _ = Group.objects.get_or_create(name='common')
        instance.groups.add(common_group)




@receiver(m2m_changed, sender=Post.categories.through)
def notify_subscribers(sender, instance, action, **kwargs):
    if action == "post_add":
        # Собираем ВСЕХ подписчиков из всех категорий поста
        subscribers = set()

        for category in instance.categories.all():
            for user in category.subscribers.all():
                subscribers.add(user)

        # Отправляем каждому 1 письмо
        for user in subscribers:
            if user.email:
                link = f"http://127.0.0.1:8000{instance.get_absolute_url()}" if hasattr(instance, "get_absolute_url") else "#"

                html_content = render_to_string(
                    'news/email_notification.html',
                    {
                        'user': user,
                        'post': instance,
                        'link': link,
                    }
                )

                msg = EmailMultiAlternatives(
                    subject=instance.title,
                    body=f'Здравствуй, {user.username}. Новая статья в твоём любимом разделе!',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )

                msg.attach_alternative(html_content, "text/html")
                msg.send()
