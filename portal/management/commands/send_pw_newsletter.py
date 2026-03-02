from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Отправляет новостную рассылку пользователям Perfect World board.'

    def add_arguments(self, parser):
        parser.add_argument('--subject', required=True, help='Тема письма')
        parser.add_argument('--message', required=True, help='Текст письма')

    def handle(self, *args, **options):
        subject = options['subject']
        message = options['message']

        users = get_user_model().objects.filter(is_active=True).exclude(email='').only('email')
        emails = [u.email for u in users if u.email]
        if not emails:
            raise CommandError('Нет активных пользователей с email для рассылки.')

        sent = 0
        for email in emails:
            msg = EmailMultiAlternatives(subject=subject, body=message, to=[email])
            msg.send(fail_silently=False)
            sent += 1

        self.stdout.write(self.style.SUCCESS(f'Отправлено писем: {sent}'))
