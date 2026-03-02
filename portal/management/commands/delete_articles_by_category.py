from django.core.management.base import BaseCommand, CommandError

from portal.models import Category, Post


class Command(BaseCommand):
    help = 'Удаляет все статьи (тип AR) в указанной категории после подтверждения.'

    def add_arguments(self, parser):
        parser.add_argument(
            'category',
            type=str,
            help='Название категории (без учета регистра).',
        )

    def handle(self, *args, **options):
        category_input = options['category'].strip()
        if not category_input:
            raise CommandError('Название категории не может быть пустым.')

        category = (
            Category.objects.filter(name__iexact=category_input)
            .order_by('id')
            .first()
        )
        if category is None:
            raise CommandError(f'Категория "{category_input}" не найдена.')

        articles_qs = Post.objects.filter(type=Post.ARTICLE, categories=category).distinct()
        articles_count = articles_qs.count()

        if articles_count == 0:
            self.stdout.write(self.style.WARNING(
                f'В категории "{category.name}" нет статей для удаления.'
            ))
            return

        answer = input(
            f'Удалить {articles_count} статей из категории "{category.name}"? '
            f'Введите "yes" для подтверждения: '
        ).strip().lower()

        if answer != 'yes':
            self.stdout.write(self.style.ERROR('Операция отменена.'))
            return

        deleted_count = articles_qs.delete()[0]
        self.stdout.write(self.style.SUCCESS(
            f'Удалено объектов: {deleted_count}. '
            f'Статьи категории "{category.name}" очищены.'
        ))
