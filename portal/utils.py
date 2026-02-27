import threading
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


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
