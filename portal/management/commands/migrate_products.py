from django.core.management.base import BaseCommand
from simpleapp.models import Product as SimpleProduct
from portal.models import Product as PortalProduct, Category


class Command(BaseCommand):
    help = 'Перенос товаров из simpleapp в portal'

    def handle(self, *args, **options):
        count = 0

        for sp in SimpleProduct.objects.all():
            category, _ = Category.objects.get_or_create(
                name=sp.category.name
            )

            PortalProduct.objects.create(
                name=sp.name,
                description=sp.description,
                price=sp.price,
                category=category,
                image=sp.image,
                rating=sp.rating,
            )

            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Перенесено товаров: {count}'
        ))
