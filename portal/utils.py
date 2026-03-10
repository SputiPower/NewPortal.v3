import threading
from django.core.mail import EmailMultiAlternatives
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q

from .models import Category


TECHNICAL_CATEGORY_PREFIXES = (
    'cat_',
    'catx_',
    'mail_cat_',
    'fb_cat_',
    'q_cat_',
    'q2_cat_',
    'queue_',
    'react_',
    'fallback_',
)

TECHNICAL_CATEGORY_EXACT = (
    'test category',
)


def get_public_categories():
    cache_key = 'portal:public-category-ids:v1'
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        if not cached_ids and Category.objects.exists():
            cache.delete(cache_key)
        else:
            preserved_order = {pk: index for index, pk in enumerate(cached_ids)}
            categories = list(Category.objects.filter(pk__in=cached_ids))
            if len(categories) == len(cached_ids):
                return sorted(categories, key=lambda item: preserved_order.get(item.pk, len(preserved_order)))
            cache.delete(cache_key)

    technical_filter = Q()
    for prefix in TECHNICAL_CATEGORY_PREFIXES:
        technical_filter |= Q(name__istartswith=prefix)
    for exact_name in TECHNICAL_CATEGORY_EXACT:
        technical_filter |= Q(name__iexact=exact_name)
    categories = list(Category.objects.exclude(technical_filter).order_by('name'))
    cache.set(cache_key, [category.pk for category in categories], timeout=60 * 15)
    return categories


def send_email_async(subject: str, body: str, to_email: list[str]):
    """
    Отправка письма в отдельном потоке.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    msg = EmailMultiAlternatives(subject, body, from_email, to_email)

    # Отправка в фоне
    threading.Thread(target=lambda: msg.send(fail_silently=False), daemon=True).start()


def send_test_email(to_email="sputi0596@gmail.com"):
    """
    Тестовое письмо для проверки работы отправки.
    """
    subject = "Тестовое письмо Django"
    body = "Если ты получил это письмо — всё работает!"
    send_email_async(subject, body, [to_email])
