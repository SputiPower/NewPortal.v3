import csv
from pathlib import Path
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView, FormView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import EmailMultiAlternatives
from django.core.cache import cache
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Count, Case, When, Value, IntegerField, F, Max, Prefetch
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.translation import gettext as _
from zoneinfo import available_timezones
from datetime import timedelta
from random import randint

from .models import (
    Post, Category, Author, Product, PostMedia, Subscription, Reaction,
    BoardAd, AdResponse, EmailVerificationCode,
)
from .forms import (
    PostForm, ProfileForm, EmailChangeForm,
    PWSignupForm, EmailCodeVerifyForm, BoardAdForm, AdResponseForm,
)
from .filters import PostFilter, ProductFilter
from .utils import get_public_categories


SYSTEM_AUTHOR_PREFIXES = ('QUEUE_', 'MAIL_', 'REACT_', 'FALLBACK_')


def _lap_to_seconds(value):
    if not value:
        return None
    minutes, seconds = value.split(':')
    return int(minutes) * 60 + float(seconds)


def _format_lap(seconds):
    if seconds is None:
        return ''
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f'{minutes}:{remainder:06.3f}'


def _build_mount_panorama_report():
    csv_path = Path.home() / 'Downloads' / 'eventresult_83727039 (1).csv'
    if not csv_path.exists():
        return None
    csv_stat = csv_path.stat()
    cache_key = f'mount-panorama-report:{csv_stat.st_mtime_ns}:{csv_stat.st_size}'
    cached_report = cache.get(cache_key)
    if cached_report is not None:
        return cached_report

    with csv_path.open('r', encoding='utf-8-sig', newline='') as source:
        rows = list(csv.reader(source))

    if len(rows) < 5:
        return None

    meta_header = rows[0]
    meta_values = rows[1]
    meta = dict(zip(meta_header, meta_values))
    result_header = rows[3]
    result_rows = [dict(zip(result_header, row)) for row in rows[4:] if row]

    team_row = next(
        (row for row in result_rows if row.get('Cust ID', '').startswith('-') and row.get('Name', '').strip().lower() in {'vodka players', 'vodka player'}),
        None,
    )
    if team_row is None:
        return None

    team_id = team_row['Team ID']
    driver_rows = [
        row for row in result_rows
        if row.get('Team ID') == team_id and not row.get('Cust ID', '').startswith('-')
    ]
    driver_rows.sort(key=lambda item: int(item.get('Laps Comp') or 0), reverse=True)

    field_rows = [
        row for row in result_rows
        if row.get('Cust ID', '').startswith('-')
    ]
    field_rows.sort(key=lambda item: int(item.get('Fin Pos') or 999))

    start_pos = int(team_row['Start Pos'])
    finish_pos = int(team_row['Fin Pos'])
    laps_completed = int(team_row['Laps Comp'])
    incidents = int(team_row['Inc'])
    best_lap = _lap_to_seconds(team_row['Fastest Lap Time'])
    avg_lap = _lap_to_seconds(team_row['Average Lap Time'])
    position_gain = start_pos - finish_pos

    strongest_driver = min(
        driver_rows,
        key=lambda item: _lap_to_seconds(item['Average Lap Time']) or 10_000,
    )
    fastest_driver = min(
        driver_rows,
        key=lambda item: _lap_to_seconds(item['Fastest Lap Time']) or 10_000,
    )

    # Aggregated CSV only contains final results, so the progression curve is modeled
    # from start/finish delta and total race distance.
    modeled_progress = []
    checkpoints = [
        (0, start_pos),
        (28, max(finish_pos + 16, start_pos - 6)),
        (92, max(finish_pos + 9, start_pos - 12)),
        (180, max(finish_pos + 4, start_pos - 18)),
        (260, max(finish_pos + 2, start_pos - 22)),
        (laps_completed, finish_pos),
    ]
    for lap in range(0, laps_completed + 1, 4):
        previous = checkpoints[0]
        current = checkpoints[-1]
        for point in checkpoints[1:]:
            if lap <= point[0]:
                current = point
                break
            previous = point
        span = max(1, current[0] - previous[0])
        progress = (lap - previous[0]) / span
        position = previous[1] + (current[1] - previous[1]) * progress
        modeled_progress.append({'lap': lap, 'position': round(position, 2)})

    pace_series = []
    for driver in driver_rows:
        avg_seconds = _lap_to_seconds(driver['Average Lap Time'])
        best_seconds = _lap_to_seconds(driver['Fastest Lap Time'])
        pace_series.append({
            'name': driver['Name'],
            'avg_seconds': avg_seconds,
            'best_seconds': best_seconds,
            'avg_lap': driver['Average Lap Time'],
            'best_lap': driver['Fastest Lap Time'],
            'laps': int(driver['Laps Comp'] or 0),
            'inc': int(driver['Inc'] or 0),
            'ir_delta': int(driver['New iRating'] or 0) - int(driver['Old iRating'] or 0),
        })

    field_delta = [
        {
            'name': row['Name'],
            'start': int(row['Start Pos'] or 0),
            'finish': int(row['Fin Pos'] or 0),
            'highlight': row['Team ID'] == team_id,
        }
        for row in field_rows
    ]

    heatmap_metrics = []
    max_laps = max(item['laps'] for item in pace_series) if pace_series else 1
    max_inc = max(item['inc'] for item in pace_series) if pace_series else 1
    min_avg = min(item['avg_seconds'] for item in pace_series) if pace_series else 1
    max_avg = max(item['avg_seconds'] for item in pace_series) if pace_series else 1
    min_best = min(item['best_seconds'] for item in pace_series) if pace_series else 1
    max_best = max(item['best_seconds'] for item in pace_series) if pace_series else 1

    def normalize(value, low, high, invert=False):
        if high == low:
            ratio = 1
        else:
            ratio = (value - low) / (high - low)
        ratio = 1 - ratio if invert else ratio
        return round(max(0, min(1, ratio)), 4)

    for item in pace_series:
        heatmap_metrics.append({
            'driver': item['name'],
            'cells': [
                {'label': 'Laps', 'value': item['laps'], 'intensity': normalize(item['laps'], 0, max_laps)},
                {'label': 'Avg Pace', 'value': item['avg_lap'], 'intensity': normalize(item['avg_seconds'], min_avg, max_avg, invert=True)},
                {'label': 'Best Lap', 'value': item['best_lap'], 'intensity': normalize(item['best_seconds'], min_best, max_best, invert=True)},
                {'label': 'Inc', 'value': item['inc'], 'intensity': normalize(item['inc'], 0, max_inc, invert=True)},
            ]
        })

    story_points = [
        {
            'phase': 'Opening Hour',
            'headline': 'Выход из глубины пелотона',
            'text': 'CSV подтверждает старт с P46 и итоговый камбэк до P22. Детальной покруговой ленты нет, но уже на первом отрезке команда начала планомерно отыгрывать позиции.',
        },
        {
            'phase': 'Middle Stints',
            'headline': 'Стабилизация темпа',
            'text': f"Самый сильный средний темп в составе показал {strongest_driver['Name']} с {strongest_driver['Average Lap Time']}.",
        },
        {
            'phase': 'Fastest Reference',
            'headline': 'Абсолютный пик скорости',
            'text': f"Лучший круг команды поставил {fastest_driver['Name']} — {fastest_driver['Fastest Lap Time']}.",
        },
        {
            'phase': 'Finish',
            'headline': 'Чистое доведение до финиша',
            'text': f"324 круга, 60 incident points и итоговое P22 в поле SOF {meta.get('Strength of Field', '')}.",
        },
    ]

    report = {
        'meta': {
            'track': meta.get('Track', 'Mount Panorama Circuit'),
            'series': meta.get('Series', 'Bathurst 12 Hour'),
            'start_time': meta.get('Start Time', ''),
            'sof': int(meta.get('Strength of Field') or 0),
        },
        'team': {
            'name': team_row['Name'],
            'car': team_row['Car'],
            'car_number': team_row['Car #'],
            'start_pos': start_pos,
            'finish_pos': finish_pos,
            'position_gain': position_gain,
            'laps_completed': laps_completed,
            'incidents': incidents,
            'best_lap': team_row['Fastest Lap Time'],
            'average_lap': team_row['Average Lap Time'],
            'interval': team_row['Interval'],
            'points': int(team_row['Pts'] or 0),
        },
        'drivers': pace_series,
        'field_delta': field_delta,
        'modeled_progress': modeled_progress,
        'heatmap': heatmap_metrics,
        'story_points': story_points,
        'track_points': [
            {'label': 'Hell Corner', 'x': 92, 'y': 320},
            {'label': 'Mountain Straight', 'x': 188, 'y': 278},
            {'label': 'Griffins Bend', 'x': 284, 'y': 228},
            {'label': 'The Cutting', 'x': 332, 'y': 174},
            {'label': 'Skyline', 'x': 424, 'y': 104},
            {'label': 'The Esses', 'x': 516, 'y': 138},
            {'label': "Forest's Elbow", 'x': 590, 'y': 236},
            {'label': 'Conrod Straight', 'x': 510, 'y': 334},
            {'label': "The Chase", 'x': 268, 'y': 370},
            {'label': "Murray's Corner", 'x': 138, 'y': 360},
        ],
        'available_columns': result_header,
        'derived': {
            'strongest_driver': strongest_driver['Name'],
            'fastest_driver': fastest_driver['Name'],
            'longest_stint_laps': max(item['laps'] for item in pace_series) if pace_series else 0,
            'driver_count': len(pace_series),
        },
    }
    cache.set(cache_key, report, timeout=60 * 30)
    return report


def exclude_system_generated_posts(queryset):
    """Hide technical/test posts from user-facing feeds."""
    author_filter = Q()
    for prefix in SYSTEM_AUTHOR_PREFIXES:
        author_filter |= Q(author__user__username__istartswith=prefix)
    return queryset.exclude(author_filter)


def _safe_redirect_target(request, fallback_name='home', *candidates):
    for candidate in candidates:
        if not candidate:
            continue
        if url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(candidate)
    return redirect(reverse(fallback_name))


# ----------------- UPGRADE ДО АВТОРА -----------------
@login_required
@require_POST
def upgrade(request):
    authors_group, _ = Group.objects.get_or_create(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        request.user.groups.add(authors_group)
    return redirect(reverse('home'))


# ----------------- ПОДПИСКА НА КАТЕГОРИЮ -----------------
@login_required
@require_POST
def subscribe_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if not category.subscribers.filter(pk=request.user.pk).exists():
        category.subscribers.add(request.user)
    Subscription.objects.get_or_create(user=request.user, category=category, author=None)
    return _safe_redirect_target(request, 'home', request.META.get('HTTP_REFERER'))


# ----------------- ОТПИСКА ОТ КАТЕГОРИИ -----------------
@login_required
@require_POST
def unsubscribe_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.subscribers.filter(pk=request.user.pk).exists():
        category.subscribers.remove(request.user)
    Subscription.objects.filter(user=request.user, category=category).delete()
    return _safe_redirect_target(request, 'home', request.META.get('HTTP_REFERER'))


@login_required
@require_POST
def subscribe_author(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    Subscription.objects.get_or_create(user=request.user, author=author, category=None)
    return _safe_redirect_target(request, 'home', request.META.get('HTTP_REFERER'))


@login_required
@require_POST
def unsubscribe_author(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    Subscription.objects.filter(user=request.user, author=author).delete()
    return _safe_redirect_target(request, 'home', request.META.get('HTTP_REFERER'))


# ----------------- ГЛАВНАЯ СТРАНИЦА -----------------
class IndexView(TemplateView):
    template_name = 'portal/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_not_author'] = True
        if user.is_authenticated:
            context['is_not_author'] = not user.groups.filter(name='authors').exists()
        context['latest_news'] = exclude_system_generated_posts(
            Post.objects.filter(type='NW').select_related('author__user').prefetch_related('media_files')
        ).order_by('-created_at')[:8]
        context['latest_articles'] = exclude_system_generated_posts(
            Post.objects.filter(type='AR').select_related('author__user').prefetch_related('media_files')
        ).order_by('-created_at')[:8]
        return context


# ----------------- BASE POST -----------------
class BasePostListView(ListView):
    paginate_by = 10
    context_object_name = 'posts'
    filter_class = None
    type_filter = None

    def get_queryset(self):
        queryset = exclude_system_generated_posts(
            Post.objects.select_related('author__user').prefetch_related('media_files', 'categories')
        ).annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.LIKE), distinct=True),
            dislikes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.DISLIKE), distinct=True),
        )
        if self.type_filter:
            queryset = queryset.filter(type=self.type_filter)
        if self.filter_class:
            self.filterset = self.filter_class(self.request.GET, queryset)
            queryset = self.filterset.qs

        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                user_reaction=Max(
                    Case(
                        When(reactions__user=self.request.user, then=F('reactions__reaction_type')),
                        default=Value(None),
                    )
                )
            )
        return queryset.order_by('-created_at').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = get_public_categories()
        if hasattr(self, 'filterset'):
            context['filterset'] = self.filterset
        return context


# ----------------- NEWS -----------------
class NewsList(BasePostListView):
    template_name = 'news/news_list.html'
    context_object_name = 'news'
    type_filter = 'NW'
    filter_class = PostFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # добавляем идентификаторы категорий, на которые подписан пользователь
        if self.request.user.is_authenticated:
            context['subscriber_category_ids'] = list(
                self.request.user.subscribed_categories.values_list('id', flat=True)
            )
        else:
            context['subscriber_category_ids'] = []
        return context


class CategoryPosts(NewsList):
    template_name = 'news/category_posts.html'
    
    def get_queryset(self):
        category_id = self.kwargs['pk']
        queryset = super().get_queryset()
        return queryset.filter(categories__id=category_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, id=self.kwargs['pk'])
        context['current_category'] = category
        context['subscriber_ids'] = list(category.subscribers.values_list('pk', flat=True))
        context['categories'] = get_public_categories()
        return context


class NewsDetail(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news_item'

    def get_queryset(self):
        queryset = Post.objects.filter(type='NW').select_related('author__user').prefetch_related('media_files').annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.LIKE), distinct=True),
            dislikes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.DISLIKE), distinct=True),
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                user_reaction=Max(
                    Case(
                        When(reactions__user=self.request.user, then=F('reactions__reaction_type')),
                        default=Value(None),
                    )
                )
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        news_item = context['news_item']
        story_title = news_item.title.lower()
        mount_report = None

        if 'mount panorama' in story_title or 'vodka players' in story_title:
            mount_report = _build_mount_panorama_report()
            context['story_kicker_text'] = 'Endurance Race Report'
            context['hero_subtitle'] = (
                'Спецматериал о 12-часовой гонке Vodka Player на Mount Panorama: '
                'камбэк с P46 на P22, темп по пилотам и аналитика выступления.'
            )
            context['story_strip_items'] = [
                {'label': 'Старт', 'value': 'P46'},
                {'label': 'Финиш', 'value': 'P22'},
                {'label': 'Прогресс', 'value': '+24 позиции'},
                {'label': 'Лучший круг', 'value': '2:03.256'},
            ]
            context['story_side_title'] = 'Что важно'
            context['story_side_text'] = (
                'Для Vodka players это была не просто длинная гонка на выносливость, '
                'а полноценный камбэк через трафик, инциденты и 324 круга Bathurst.'
            )
            context['story_fact_items'] = [
                {'label': 'Трек', 'value': 'Mount Panorama Circuit'},
                {'label': 'Эвент', 'value': 'Bathurst 12 Hour'},
                {'label': 'Команда', 'value': 'Vodka players'},
                {'label': 'Дистанция', 'value': '324 круга'},
            ]
        elif 'ufc' in story_title or 'оливейра' in story_title or 'холлоуэ' in story_title:
            context['story_kicker_text'] = 'Fight Night Breakdown'
            context['hero_subtitle'] = ''
            context['story_strip_items'] = [
                {'label': 'Статус', 'value': 'Главный бой UFC 326'},
                {'label': 'Результат', 'value': 'Оливейра def. Холлоуэй'},
                {'label': 'Метод', 'value': 'Единогласное решение'},
                {'label': 'Счет судей', 'value': '50-45, 50-45, 50-45'},
            ]
            context['story_side_title'] = 'Что важно'
            context['story_side_text'] = (
                'Это был бой, который снова вернул Оливейру в центр большой титульной '
                'картины UFC.'
            )
            context['story_fact_items'] = [
                {'label': 'Турнир', 'value': 'UFC 326'},
                {'label': 'Арена', 'value': 'T-Mobile Arena, Лас-Вегас'},
                {'label': 'На кону', 'value': 'BMF-титул'},
                {'label': 'Контекст', 'value': 'Реванш спустя почти 11 лет'},
            ]
        else:
            context['story_kicker_text'] = 'Feature Story'
            context['hero_subtitle'] = ''
            context['story_strip_items'] = [
                {'label': 'Публикация', 'value': news_item.created_at.strftime('%d.%m.%Y')},
                {'label': 'Автор', 'value': news_item.author.user.username},
                {'label': 'Формат', 'value': 'Новость'},
                {'label': 'Рейтинг', 'value': str(news_item.rating)},
            ]
            context['story_side_title'] = 'Что важно'
            context['story_side_text'] = 'Ключевой контекст и основные факты по публикации.'
            context['story_fact_items'] = [
                {'label': 'Формат', 'value': 'Новость'},
                {'label': 'Дата', 'value': news_item.created_at.strftime('%d.%m.%Y %H:%M')},
            ]
        context['mount_report'] = mount_report

        if self.request.user.is_authenticated:
            context['is_author_subscribed'] = Subscription.objects.filter(
                user=self.request.user, author=news_item.author
            ).exists()
        else:
            context['is_author_subscribed'] = False
        return context


# ----------------- ARTICLES -----------------
class ArticleList(BasePostListView):
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 5
    type_filter = 'AR'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset


class ArticleDetail(DetailView):
    model = Post
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        queryset = Post.objects.filter(type='AR').select_related('author__user').prefetch_related('media_files').annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.LIKE), distinct=True),
            dislikes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.DISLIKE), distinct=True),
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                user_reaction=Max(
                    Case(
                        When(reactions__user=self.request.user, then=F('reactions__reaction_type')),
                        default=Value(None),
                    )
                )
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = context['article']
        if self.request.user.is_authenticated:
            context['is_author_subscribed'] = Subscription.objects.filter(
                user=self.request.user, author=article.author
            ).exists()
        else:
            context['is_author_subscribed'] = False
        return context


# ----------------- CREATE POST -----------------
class NewsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'portal/post_create.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['require_images'] = True
        kwargs['max_images'] = 3
        return kwargs

    def form_valid(self, form):
        # ограничение: не больше трёх новостей за последние 24 часа
        author, _created = Author.objects.get_or_create(user=self.request.user)
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=1)
        recent_count = Post.objects.filter(
            author=author, type='NW', created_at__gte=cutoff
        ).count()
        if recent_count >= 3:
            form.add_error(None, _('Вы уже опубликовали 3 новости за последние 24 часа'))
            return self.form_invalid(form)

        form.instance.author = author
        form.instance.type = 'NW'
        response = super().form_valid(form)
        for image in form.cleaned_data.get('images', []):
            PostMedia.objects.create(post=self.object, image=image)
        return response


class ArticleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'portal/post_create.html'
    success_url = reverse_lazy('article_list')

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['require_images'] = True
        kwargs['max_images'] = 3
        return kwargs

    def form_valid(self, form):
        author, _ = Author.objects.get_or_create(user=self.request.user)
        form.instance.author = author
        form.instance.type = 'AR'
        response = super().form_valid(form)
        for image in form.cleaned_data.get('images', []):
            PostMedia.objects.create(post=self.object, image=image)
        return response


# ----------------- UPDATE POST -----------------
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'portal/post_edit.html'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(author__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['require_images'] = False
        kwargs['max_images'] = 3
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.cleaned_data.get('images', []):
            PostMedia.objects.create(post=self.object, image=image)
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


# ----------------- DELETE POST -----------------
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'portal/post_delete.html'

    def test_func(self):
        post = self.get_object()
        return (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or post.author.user_id == self.request.user.id
        )

    def get_queryset(self):
        return Post.objects.select_related('author__user')

    def dispatch(self, request, *args, **kwargs):
        self._cached_object = self.get_queryset().filter(pk=kwargs.get('pk')).first()
        if self._cached_object is None:
            messages.info(request, _('Пост уже удален.'))
            return redirect('news_list')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if hasattr(self, '_cached_object') and self._cached_object is not None:
            return self._cached_object
        return super().get_object(queryset)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        cache.delete(f'article-{self.object.pk}')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        if self.object.type == Post.ARTICLE:
            return reverse_lazy('article_list')
        return reverse_lazy('news_list')


# ----------------- LIKE -----------------
@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.like()
    return _safe_redirect_target(request, 'home', request.META.get('HTTP_REFERER'))


@require_POST
def react_post(request, post_id):
    if not request.user.is_authenticated:
        login_url = f"{reverse('account_login')}?next={request.get_full_path()}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'auth_required', 'login_url': login_url}, status=401)
        return redirect(login_url)

    post = get_object_or_404(Post, pk=post_id)
    reaction_type = request.POST.get('reaction_type')
    if reaction_type not in {Reaction.LIKE, Reaction.DISLIKE}:
        return JsonResponse({'ok': False, 'error': 'invalid_reaction'}, status=400)

    reaction, created = Reaction.objects.get_or_create(
        user=request.user,
        post=post,
        defaults={'reaction_type': reaction_type},
    )
    if not created and reaction.reaction_type != reaction_type:
        reaction.reaction_type = reaction_type
        reaction.save(update_fields=['reaction_type', 'updated_at'])

    likes_count = post.reactions.filter(reaction_type=Reaction.LIKE).count()
    dislikes_count = post.reactions.filter(reaction_type=Reaction.DISLIKE).count()
    # NOTE: modeltranslation queryset in this project is incompatible with
    # Django 6 save(update_fields=...) path for translated models.
    # Update rating through queryset update to avoid MultilingualQuerySet._update crash.
    post_rating = likes_count - dislikes_count
    Post.objects.filter(pk=post.pk).update(rating=post_rating)

    return JsonResponse({
        'ok': True,
        'reaction': reaction_type,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'rating': post_rating,
    })


@login_required
def profile_view(request):
    user = request.user
    profile_form = ProfileForm(instance=user)
    email_form = EmailChangeForm(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            profile_form = ProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _('Профиль обновлён.'))
                return redirect('profile')
        elif action == 'change_email':
            email_form = EmailChangeForm(user, request.POST)
            if email_form.is_valid():
                user.email = email_form.cleaned_data['email']
                user.save(update_fields=['email'])
                messages.success(request, _('Email успешно изменён.'))
                return redirect('profile')

    user_author = Author.objects.filter(user=user).first()
    my_news = Post.objects.filter(author__user=user).select_related('author__user').order_by('-created_at')
    my_news_count = my_news.filter(type=Post.NEWS).count()
    liked_news = Post.objects.filter(
        type=Post.NEWS,
        reactions__user=user,
        reactions__reaction_type=Reaction.LIKE
    ).select_related('author__user').distinct().order_by('-created_at')[:20]
    category_subscriptions = Subscription.objects.filter(user=user, category__isnull=False).select_related('category')
    author_subscriptions = Subscription.objects.filter(user=user, author__isnull=False).select_related('author__user')

    return render(request, 'profile.html', {
        'profile_form': profile_form,
        'email_form': email_form,
        'my_news': my_news[:20],
        'my_news_count': my_news_count,
        'liked_news': liked_news,
        'category_subscriptions': category_subscriptions,
        'author_subscriptions': author_subscriptions,
        'user_author': user_author,
    })


@login_required
def change_email_view(request):
    form = EmailChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.email = form.cleaned_data['email']
        request.user.save(update_fields=['email'])
        messages.success(request, _('Email успешно изменён.'))
        return redirect('profile')
    return render(request, 'account/email_change.html', {'form': form})


@require_POST
def set_timezone_view(request):
    tzname = request.POST.get('timezone')
    if tzname and tzname in available_timezones():
        request.session['django_timezone'] = tzname
    return _safe_redirect_target(
        request,
        'home',
        request.POST.get('next'),
        request.META.get('HTTP_REFERER'),
    )


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.success(self.request, _('Пароль успешно изменён.'))
        return super().form_valid(form)


class SmartFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'feed.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        subscribed_category_ids = list(
            Subscription.objects.filter(user=user, category__isnull=False).values_list('category_id', flat=True)
        )
        subscribed_author_ids = list(
            Subscription.objects.filter(user=user, author__isnull=False).values_list('author_id', flat=True)
        )
        liked_category_ids = list(
            Category.objects.filter(
                posts__reactions__user=user,
                posts__reactions__reaction_type=Reaction.LIKE
            ).values_list('id', flat=True).distinct()
        )
        recent_cutoff = timezone.now() - timedelta(days=2)

        queryset = Post.objects.filter(type=Post.NEWS).select_related('author__user').prefetch_related('media_files').annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.LIKE), distinct=True),
            dislikes_count=Count('reactions', filter=Q(reactions__reaction_type=Reaction.DISLIKE), distinct=True),
            category_match=Count('categories', filter=Q(categories__in=subscribed_category_ids), distinct=True),
            author_match=Case(
                When(author_id__in=subscribed_author_ids, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            similar_match=Count('categories', filter=Q(categories__in=liked_category_ids), distinct=True),
            recent_bonus=Case(
                When(created_at__gte=recent_cutoff, then=Value(2)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            user_reaction=Max(
                Case(
                    When(reactions__user=user, then=F('reactions__reaction_type')),
                    default=Value(None),
                )
            ),
        ).annotate(
            relevance_score=(
                F('category_match') * Value(5) +
                F('author_match') * Value(7) +
                F('similar_match') * Value(3) +
                F('likes_count') * Value(2) -
                F('dislikes_count') +
                F('recent_bonus')
            ),
            popularity_score=(F('likes_count') * Value(2) - F('dislikes_count')),
        ).distinct()

        sort = self.request.GET.get('sort', 'relevance')
        if sort == 'popular':
            return queryset.order_by('-popularity_score', '-created_at')
        if sort == 'date':
            return queryset.order_by('-created_at')
        return queryset.order_by('-relevance_score', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort'] = self.request.GET.get('sort', 'relevance')
        return context


# ----------------- PERFECT WORLD BOARD -----------------
def _send_verification_code_email(user, code):
    subject = 'Perfect World: код подтверждения регистрации'
    body = (
        f'Здравствуйте, {user.username}!\n\n'
        f'Ваш код подтверждения: {code}\n'
        'Код действует 15 минут.\n\n'
        'Если вы не регистрировались, просто проигнорируйте это письмо.'
    )
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.send()


class PWSignupView(FormView):
    template_name = 'pw/signup.html'
    form_class = PWSignupForm
    success_url = reverse_lazy('pw_verify_email')

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.is_active = False
            user.save()

            code = f'{randint(0, 999999):06d}'
            EmailVerificationCode.objects.update_or_create(
                user=user,
                defaults={
                    'code': code,
                    'expires_at': timezone.now() + timedelta(minutes=15),
                    'is_used': False,
                },
            )
        _send_verification_code_email(user, code)
        messages.info(self.request, 'Код подтверждения отправлен на указанную почту.')
        return super().form_valid(form)


class PWVerifyEmailCodeView(FormView):
    template_name = 'pw/verify_email.html'
    form_class = EmailCodeVerifyForm
    success_url = reverse_lazy('pw_ad_list')

    def form_valid(self, form):
        email = form.cleaned_data['email'].strip().lower()
        code = form.cleaned_data['code'].strip()

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            form.add_error('email', 'Пользователь с таким email не найден.')
            return self.form_invalid(form)

        code_obj = EmailVerificationCode.objects.filter(user=user).first()
        if code_obj is None:
            form.add_error('code', 'Код не найден. Запросите регистрацию повторно.')
            return self.form_invalid(form)
        if code_obj.is_used:
            form.add_error('code', 'Этот код уже использован.')
            return self.form_invalid(form)
        if code_obj.is_expired():
            form.add_error('code', 'Срок действия кода истек. Зарегистрируйтесь заново.')
            return self.form_invalid(form)
        if code_obj.code != code:
            form.add_error('code', 'Неверный код подтверждения.')
            return self.form_invalid(form)

        user.is_active = True
        user.save(update_fields=['is_active'])
        code_obj.is_used = True
        code_obj.save(update_fields=['is_used'])
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, 'Email подтвержден. Добро пожаловать в Perfect World Board.')
        return super().form_valid(form)


class PWAdListView(ListView):
    model = BoardAd
    template_name = 'pw/ad_list.html'
    context_object_name = 'ads'
    paginate_by = 10

    def get_queryset(self):
        queryset = BoardAd.objects.select_related('author')
        category = self.request.GET.get('category')
        search = self.request.GET.get('q')
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = BoardAd.CATEGORY_CHOICES
        context['selected_category'] = self.request.GET.get('category', '')
        context['q'] = self.request.GET.get('q', '')
        return context


class PWAdDetailView(DetailView):
    model = BoardAd
    template_name = 'pw/ad_detail.html'
    context_object_name = 'ad'

    def get_queryset(self):
        return BoardAd.objects.select_related('author').prefetch_related(
            Prefetch('responses', queryset=AdResponse.objects.select_related('author').order_by('-created_at'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response_form'] = AdResponseForm()
        context['responses'] = self.object.responses.all()
        return context


class PWAdCreateView(LoginRequiredMixin, CreateView):
    model = BoardAd
    form_class = BoardAdForm
    template_name = 'pw/ad_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Объявление опубликовано.')
        return super().form_valid(form)


class PWAdUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BoardAd
    form_class = BoardAdForm
    template_name = 'pw/ad_form.html'

    def test_func(self):
        return self.get_object().author_id == self.request.user.id

    def form_valid(self, form):
        messages.success(self.request, 'Объявление обновлено.')
        return super().form_valid(form)


class PWAdDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BoardAd
    template_name = 'pw/ad_delete.html'
    success_url = reverse_lazy('pw_ad_list')

    def test_func(self):
        return self.get_object().author_id == self.request.user.id

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Объявление удалено.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def create_ad_response(request, pk):
    ad = get_object_or_404(BoardAd, pk=pk)
    if ad.author_id == request.user.id:
        messages.error(request, 'Нельзя отправить отклик на собственное объявление.')
        return redirect(ad.get_absolute_url())

    form = AdResponseForm(request.POST)
    if form.is_valid():
        response, created = AdResponse.objects.get_or_create(
            ad=ad,
            author=request.user,
            defaults={'text': form.cleaned_data['text']},
        )
        if not created:
            response.text = form.cleaned_data['text']
            response.save(update_fields=['text'])
            messages.info(request, 'Ваш отклик обновлен.')
        else:
            messages.success(request, 'Отклик отправлен.')
    else:
        messages.error(request, 'Не удалось отправить отклик. Проверьте текст.')
    return redirect(ad.get_absolute_url())


class MyAdResponsesView(LoginRequiredMixin, TemplateView):
    template_name = 'pw/my_responses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        my_ads = BoardAd.objects.filter(author=self.request.user).only('id', 'title').order_by('-created_at')
        selected_ad_id = self.request.GET.get('ad')
        responses = AdResponse.objects.select_related('author', 'ad').filter(ad__author=self.request.user)
        if selected_ad_id:
            responses = responses.filter(ad_id=selected_ad_id)

        context['my_ads'] = my_ads
        context['responses'] = responses
        context['selected_ad_id'] = selected_ad_id or ''
        return context


@login_required
@require_POST
def accept_ad_response(request, pk):
    response = get_object_or_404(AdResponse.objects.select_related('ad'), pk=pk)
    if response.ad.author_id != request.user.id:
        messages.error(request, 'Недостаточно прав.')
        return redirect('pw_my_responses')

    response.is_accepted = True
    response.save(update_fields=['is_accepted'])
    messages.success(request, 'Отклик принят. Пользователь уведомлен по email.')
    return redirect('pw_my_responses')


@login_required
@require_POST
def delete_ad_response(request, pk):
    response = get_object_or_404(AdResponse.objects.select_related('ad'), pk=pk)
    if response.ad.author_id != request.user.id:
        messages.error(request, 'Недостаточно прав.')
        return redirect('pw_my_responses')

    response.delete()
    messages.success(request, 'Отклик удален.')
    return redirect('pw_my_responses')


# ----------------- PRODUCTS -----------------
class ProductList(ListView):
    model = Product
    template_name = 'products/products_list.html'
    context_object_name = 'products'
    paginate_by = 6

    def get_queryset(self):
        queryset = Product.objects.select_related('category').order_by('-id')
        self.filterset = ProductFilter(self.request.GET or None, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['categories'] = get_public_categories()
        return context


class ProductDetail(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.select_related('category')


# ----------------- NEWS SEARCH -----------------
class NewsSearchView(BasePostListView):
    template_name = 'news/news_search.html'
    context_object_name = 'news'
    type_filter = 'NW'
    filter_class = PostFilter
    paginate_by = 10


# ----------------- STATIC / TEST -----------------
def word_box_view(request):
    return render(request, 'portal/word_box.html')


from .utils import send_test_email
@staff_member_required
@require_POST
def test_email_view(request):
    send_test_email()  # отправка в фоне
    return render(request, "portal/test_email.html", {"message": "✅ Письмо отправляется в фоне! Проверь почту через несколько секунд."})
