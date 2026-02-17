from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ----------------- AUTHOR -----------------
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
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
    name = models.CharField(max_length=64, unique=True)

    # 🔥 Подписчики категории (для email-рассылки)
    subscribers = models.ManyToManyField(
        User,
        related_name='subscribed_categories',
        blank=True
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

    categories = models.ManyToManyField(
        Category,
        through='PostCategory',
        related_name='posts'
    )

    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)

    # Картинка поста
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

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
