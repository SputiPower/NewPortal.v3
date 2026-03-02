import random
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.cache import cache
from django.utils import timezone
from django.apps import apps  # Для динамического импорта Comment
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


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
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')


# ----------------- POST -----------------
class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    TYPES = [
        (ARTICLE, _('Статья')),
        (NEWS, _('Новость')),
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

    def get_absolute_url(self):
        if self.type == self.ARTICLE:
            return reverse('article_detail', kwargs={'pk': self.pk})
        return reverse('news_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Пост')
        verbose_name_plural = _('Посты')

    def save(self, *args, **kwargs):
        # Уведомления подписчиков отправляются из m2m_changed-сигнала
        # после назначения категорий посту.
        super().save(*args, **kwargs)
        if self.type == self.ARTICLE:
            cache.delete(f'article-{self.pk}')


# ----------------- POST CATEGORY -----------------
class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.post.title} → {self.category.name}'

    class Meta:
        verbose_name = _('Связь поста и категории')
        verbose_name_plural = _('Связи постов и категорий')


class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_files')
    image = models.ImageField(
        upload_to='posts/gallery/',
        validators=[FileExtensionValidator(allowed_extensions=['png'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'PNG #{self.pk} для поста {self.post_id}'

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Файл поста')
        verbose_name_plural = _('Файлы поста')


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='subscriptions',
        null=True, blank=True
    )
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='subscriptions',
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.category_id:
            return f'{self.user.username} -> category:{self.category.name}'
        return f'{self.user.username} -> author:{self.author.user.username}'

    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(category__isnull=False) & models.Q(author__isnull=True)) |
                    (models.Q(category__isnull=True) & models.Q(author__isnull=False))
                ),
                name='subscription_single_target',
            ),
            models.UniqueConstraint(
                fields=['user', 'category'],
                condition=models.Q(category__isnull=False),
                name='uniq_user_category_subscription',
            ),
            models.UniqueConstraint(
                fields=['user', 'author'],
                condition=models.Q(author__isnull=False),
                name='uniq_user_author_subscription',
            ),
        ]


class Reaction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    REACTION_CHOICES = [
        (LIKE, _('Like')),
        (DISLIKE, _('Dislike')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=7, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}:{self.post_id}:{self.reaction_type}'

    class Meta:
        verbose_name = _('Реакция')
        verbose_name_plural = _('Реакции')
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='uniq_user_post_reaction'),
        ]


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
        verbose_name = _('Комментарий')
        verbose_name_plural = _('Комментарии')


class BoardAd(models.Model):
    CATEGORY_TANKS = 'tanks'
    CATEGORY_HEALS = 'heals'
    CATEGORY_DD = 'dd'
    CATEGORY_TRADERS = 'traders'
    CATEGORY_GUILDMASTERS = 'guildmasters'
    CATEGORY_QUESTGIVERS = 'questgivers'
    CATEGORY_BLACKSMITHS = 'blacksmiths'
    CATEGORY_LEATHERWORKERS = 'leatherworkers'
    CATEGORY_ALCHEMISTS = 'alchemists'
    CATEGORY_SPELLMASTERS = 'spellmasters'

    CATEGORY_CHOICES = [
        (CATEGORY_TANKS, _('Танки')),
        (CATEGORY_HEALS, _('Хилы')),
        (CATEGORY_DD, _('ДД')),
        (CATEGORY_TRADERS, _('Торговцы')),
        (CATEGORY_GUILDMASTERS, _('Гилдмастеры')),
        (CATEGORY_QUESTGIVERS, _('Квестгиверы')),
        (CATEGORY_BLACKSMITHS, _('Кузнецы')),
        (CATEGORY_LEATHERWORKERS, _('Кожевники')),
        (CATEGORY_ALCHEMISTS, _('Зельевары')),
        (CATEGORY_SPELLMASTERS, _('Мастера заклинаний')),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='board_ads')
    title = models.CharField(max_length=255)
    content = models.TextField(help_text=_('Поддерживается форматирование и вставка ссылок/медиа.'))
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Объявление')
        verbose_name_plural = _('Объявления')

    def __str__(self):
        return f'{self.title} ({self.get_category_display()})'

    def get_absolute_url(self):
        return reverse('pw_ad_detail', kwargs={'pk': self.pk})


class AdResponse(models.Model):
    ad = models.ForeignKey(BoardAd, on_delete=models.CASCADE, related_name='responses')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ad_responses')
    text = models.TextField()
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Отклик')
        verbose_name_plural = _('Отклики')
        constraints = [
            models.UniqueConstraint(fields=['ad', 'author'], name='uniq_response_per_ad_author'),
        ]

    def __str__(self):
        return f'#{self.pk} {self.author.username} -> {self.ad_id}'


class EmailVerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Код подтверждения email')
        verbose_name_plural = _('Коды подтверждения email')

    def __str__(self):
        return f'{self.user.username}: {self.code}'

    def is_expired(self):
        return timezone.now() >= self.expires_at


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
        verbose_name = _('Продукт')
        verbose_name_plural = _('Продукты')
