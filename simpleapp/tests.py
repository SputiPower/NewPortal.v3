from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ProductPagesTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='gadgets')
        self.product = Product.objects.create(
            name='vision display',
            description='Подробное описание товара для проверки рендера и форм.',
            quantity=5,
            category=self.category,
            price=199.99,
        )

    def test_product_list_renders(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Каталог товаров')
        self.assertContains(response, self.product.name)

    def test_product_detail_renders(self):
        response = self.client.get(reverse('product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.category.name)

    def test_product_create_page_renders(self):
        response = self.client.get(reverse('product_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Создать товар')

    def test_product_get_absolute_url(self):
        self.assertEqual(self.product.get_absolute_url(), reverse('product_detail', args=[self.product.pk]))


class SwaggerUiPageTests(TestCase):
    def test_swagger_ui_page_renders(self):
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger-ui', html=False)
