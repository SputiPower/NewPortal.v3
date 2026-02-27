import random
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.apps import apps  # Для динамического импорта Comment
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


# ----------------- AUTHOR -----------------
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    instagram = models.CharField(max_length=255, blank=True, null=True)
    telegram = models.CharField(max_length=255, blank=True, null=True)

    def update_rating(self):
        """Обновление рейтинга автора: посты, комментарии, комментарии к его постам"""
        Comment = apps.get_model('portal', 'Comment')

        post_rating = sum(self.post_set.values_list('rating', flat=True)) * 3
        comment_rating = sum(self.user.comment_set.values_list('rating', flat=True))
        post_comment_rating = sum(
            Comment.objects.filter(post__author=self).values_list('rating', flat=True)
        )

        self.rating = post_rating + comment_rating + post_comment_rating
        self.save()

    def __str__(self):
        return self.user.username


# ----------------- CATEGORY -----------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7)
    subscribers = models.ManyToManyField(
        User,
        blank=True,
        related_name='subscribed_categories'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


# ----------------- POST -----------------
class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    categories = models.ManyToManyField(
        Category,
        through='PostCategory',
        related_name='posts'
    )

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def preview(self):
        return self.text[:124] + '...'

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def save(self, *args, **kwargs):
        new_instance = self.pk is None  # True, если пост создаётся впервые
        super().save(*args, **kwargs)

        # Отправка уведомления подписчикам категорий при создании нового поста
        if new_instance:
            for category in self.categories.all():
                subscribers = category.subscribers.all()
                for user in subscribers:
                    html_content = render_to_string(
                        'emails/new_article.html',
                        {
                            'user': user,
                            'news': self,
                            'category': category,
                        }
                    )
                    msg = EmailMultiAlternatives(
                        subject=self.title,
                        body=f"Здравствуй, {user.username}. Новая статья в твоём любимом разделе!",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()


# ----------------- POST CATEGORY -----------------
class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.post.title} → {self.category.name}'

    class Meta:
        verbose_name = 'Связь поста и категории'
        verbose_name_plural = 'Связи постов и категорий'


# ----------------- COMMENT -----------------
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def __str__(self):
        return f'{self.user.username}: {self.text[:20]}'

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


# ----------------- PRODUCT -----------------
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'