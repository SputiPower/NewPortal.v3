from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext

from .models import Category, Author, Post
from .models import Reaction
from .templatetags.censor import render_post_text
from .templatetags.moderation import sanitize_rich_html
from .utils import get_public_categories


PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR'
    b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00'
    b'\x90wS\xde'
    b'\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\x8f\xa4\x1d'
    b'\x00\x00\x00\x00IEND\xaeB`\x82'
)


def make_png(name='test.png'):
    return SimpleUploadedFile(name, PNG_1X1, content_type='image/png')


def make_mp4(name='preview.mp4'):
    return SimpleUploadedFile(name, b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom', content_type='video/mp4')


class SubscriptionTests(TestCase):
    def setUp(self):
        # create a user and a category
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pwd')
        self.category = Category.objects.create(name='Тест', color='#000000')
        self.client = Client()

    def test_subscribe_and_unsubscribe(self):
        self.client.force_login(self.user)
        # subscribe
        response = self.client.post(reverse('subscribe_category', args=[self.category.pk]), follow=True)
        self.assertTrue(self.user in self.category.subscribers.all())
        # unsubscribe
        response = self.client.post(reverse('unsubscribe_category', args=[self.category.pk]), follow=True)
        self.assertFalse(self.user in self.category.subscribers.all())


class CategoryCacheTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_public_categories_cache_invalidates_on_save(self):
        Category.objects.create(name='Alpha', color='#000000')
        first = get_public_categories()
        self.assertEqual(len(first), 1)

        Category.objects.create(name='Beta', color='#111111')
        refreshed = get_public_categories()
        self.assertEqual(len(refreshed), 2)


class PostCreationRulesTests(TestCase):
    def setUp(self):
        # author group and user
        self.user = User.objects.create_user(username='anna', email='anna@example.com', password='pwd')
        grp, _ = Group.objects.get_or_create(name='authors')
        self.user.groups.add(grp)
        # subscriber to category
        self.category = Category.objects.create(name='Новости', color='#ff0000')
        self.category.subscribers.add(self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def test_news_creation_requires_png_and_creates_post(self):
        url = reverse('news_create')
        data = {
            'title': 'Заголовок',
            'text': 'Текст новости очень длинный, чтобы получился предварительный фрагмент.',
            'type': 'NW',
            'categories': [self.category.pk],
            'images': [make_png()],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        created = Post.objects.filter(author__user=self.user, type='NW').order_by('-id').first()
        self.assertIsNotNone(created)
        self.assertEqual(created.title, 'Заголовок')
        self.assertEqual(created.categories.count(), 1)
        self.assertEqual(created.categories.first().pk, self.category.pk)

    def test_three_news_limit(self):
        # ensure user cannot create more than 3 news per day
        self.client.force_login(self.user)
        url = reverse('news_create')
        for i in range(3):
            response = self.client.post(url, {
                'title': f'Title {i}',
                'text': 'text',
                'type': 'NW',
                'categories': [self.category.pk],
                'images': [make_png(f'n{i}.png')],
            })
            self.assertEqual(response.status_code, 302)
        # fourth attempt should fail and display error
        response = self.client.post(url, {
            'title': 'Fourth',
            'text': 'text',
            'type': 'NW',
            'categories': [self.category.pk],
            'images': [make_png('n4.png')],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вы уже опубликовали 3 новости за последние 24 часа')
        self.assertEqual(Post.objects.filter(author__user=self.user, type='NW').count(), 3)


class PostDeleteFlowTests(TestCase):
    def setUp(self):
        self.author_user = User.objects.create_user(username='author', email='author@example.com', password='pwd')
        self.admin_user = User.objects.create_user(username='admin', email='admin@local.dev', password='pwd')
        self.admin_user.is_staff = True
        self.admin_user.save(update_fields=['is_staff'])
        self.author, _ = Author.objects.get_or_create(user=self.author_user)
        self.post = Post.objects.create(
            author=self.author,
            type=Post.NEWS,
            title='Удаляемый пост',
            text='text',
        )
        self.client = Client()

    def test_admin_can_delete_post_and_second_delete_redirects(self):
        self.client.force_login(self.admin_user)

        delete_url = reverse('post_delete', args=[self.post.pk])
        detail_url = reverse('news_detail', args=[self.post.pk])

        page = self.client.get(delete_url)
        self.assertEqual(page.status_code, 200)

        delete_response = self.client.post(delete_url)
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(delete_response.url, reverse('news_list'))

        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
        self.assertEqual(self.client.get(detail_url).status_code, 404)

        second = self.client.get(delete_url)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(second.url, reverse('news_list'))


class RedirectSafetyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='safeuser', email='safe@local.dev', password='pwd')
        self.category = Category.objects.create(name='Безопасность', color='#111111')
        self.client = Client()
        self.client.force_login(self.user)

    def test_set_timezone_ignores_external_next(self):
        response = self.client.post(reverse('set_timezone'), {
            'timezone': 'UTC',
            'next': 'https://evil.example/path',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_subscribe_category_ignores_external_referer(self):
        response = self.client.post(
            reverse('subscribe_category', args=[self.category.pk]),
            HTTP_REFERER='https://evil.example/path',
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))


class RenderPostTextFilterTests(TestCase):
    def test_render_post_text_normalizes_html_fragments(self):
        raw = '<p>One<br>Two</p><p>Three</p>'
        rendered = render_post_text(raw)
        self.assertEqual(rendered, 'One\nTwo\n\nThree')


class SanitizeRichHtmlTests(TestCase):
    def test_sanitize_rich_html_strips_script_and_event_handlers(self):
        raw = '<p>Hello</p><script>alert(1)</script><a href="javascript:alert(1)" onclick="x()">go</a>'
        rendered = str(sanitize_rich_html(raw))
        self.assertIn('<p>Hello</p>', rendered)
        self.assertNotIn('<script', rendered.lower())
        self.assertNotIn('onclick=', rendered.lower())
        self.assertNotIn('javascript:', rendered.lower())

    def test_sanitize_rich_html_keeps_safe_markup(self):
        raw = '<p>Hi <strong>there</strong> <a href="https://example.com" target="_blank">link</a></p>'
        rendered = str(sanitize_rich_html(raw))
        self.assertIn('<strong>there</strong>', rendered)
        self.assertIn('href="https://example.com"', rendered)
        self.assertIn('rel="noopener noreferrer"', rendered)


class QueryBudgetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='queryuser', email='query@local.dev', password='pwd')
        self.author, _ = Author.objects.get_or_create(user=self.user)
        self.category = Category.objects.create(name='Производительность', color='#224466')
        for i in range(6):
            post = Post.objects.create(
                author=self.author,
                type=Post.NEWS,
                title=f'Post {i}',
                text='text',
            )
            post.categories.add(self.category)
        for i in range(6):
            article = Post.objects.create(
                author=self.author,
                type=Post.ARTICLE,
                title=f'Article {i}',
                text='text',
            )
            article.categories.add(self.category)
        self.client = Client()

    def test_news_list_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 20)

    def test_news_detail_query_budget(self):
        post = Post.objects.filter(type=Post.NEWS).first()
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('news_detail', args=[post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 16)

    def test_article_list_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 18)

    def test_article_detail_query_budget(self):
        article = Post.objects.filter(type=Post.ARTICLE).first()
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('article_detail', args=[article.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 14)


class VideoPreviewRenderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='videouser', email='video@local.dev', password='pwd')
        self.author, _ = Author.objects.get_or_create(user=self.user)
        self.category = Category.objects.create(name='Спорт', color='#ff6600')
        self.post = Post.objects.create(
            author=self.author,
            type=Post.NEWS,
            title='Видео-превью',
            text='Текст новости',
            preview_video=make_mp4(),
        )
        self.post.categories.add(self.category)
        self.client = Client()

    def test_category_page_renders_video_preview(self):
        response = self.client.get(reverse('category_posts', args=[self.category.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<video', html=False)

    def test_news_detail_renders_video_preview(self):
        response = self.client.get(reverse('news_detail', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<video', html=False)


class ReactionFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reactor', email='reactor@local.dev', password='strong-password-123')
        self.author, _ = Author.objects.get_or_create(user=self.user)
        self.category = Category.objects.create(name='Спорт', color='#e93952')
        self.post = Post.objects.create(
            author=self.author,
            type=Post.NEWS,
            title='Реакция на бой',
            text='Текст',
        )
        self.post.categories.add(self.category)
        self.article = Post.objects.create(
            author=self.author,
            type=Post.ARTICLE,
            title='Аналитика боя',
            text='Текст статьи',
        )
        self.article.categories.add(self.category)
        self.client = Client()

    def test_ajax_react_requires_authentication(self):
        response = self.client.post(
            reverse('react_post', args=[self.post.pk]),
            {'reaction_type': 'like'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'auth_required')

    def test_authenticated_like_updates_counts(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('react_post', args=[self.post.pk]),
            {'reaction_type': 'like'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['likes_count'], 1)
        self.assertEqual(response.json()['dislikes_count'], 0)
        self.assertTrue(Reaction.objects.filter(user=self.user, post=self.post, reaction_type='like').exists())

    def test_authenticated_dislike_switches_existing_reaction(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse('react_post', args=[self.post.pk]),
            {'reaction_type': 'like'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        response = self.client.post(
            reverse('react_post', args=[self.post.pk]),
            {'reaction_type': 'dislike'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['likes_count'], 0)
        self.assertEqual(response.json()['dislikes_count'], 1)
        self.assertEqual(Reaction.objects.get(user=self.user, post=self.post).reaction_type, 'dislike')

    def test_authenticated_pages_render_reaction_controls(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('category_posts', args=[self.category.pk]))
        self.assertContains(response, 'data-react-btn', html=False)
        response = self.client.get(reverse('news_list'))
        self.assertContains(response, 'data-react-btn', html=False)
        response = self.client.get(reverse('news_detail', args=[self.post.pk]))
        self.assertContains(response, 'data-react-btn', html=False)
        response = self.client.get(reverse('article_detail', args=[self.article.pk]))
        self.assertContains(response, 'data-react-btn', html=False)
        response = self.client.get(reverse('smart_feed'))
        self.assertContains(response, 'data-react-btn', html=False)

    def test_anonymous_pages_show_login_prompt_instead_of_reaction_controls(self):
        response = self.client.get(reverse('category_posts', args=[self.category.pk]))
        self.assertNotContains(response, 'data-react-btn', html=False)
        self.assertContains(response, 'Войти, чтобы оценить')
        response = self.client.get(reverse('news_list'))
        self.assertNotContains(response, 'data-react-btn', html=False)
        self.assertContains(response, 'Войти, чтобы оценить')


@override_settings(
    ACCOUNT_RATE_LIMITS={
        'login': '100000/m',
        'login_failed': '100000/m',
        'signup': '100000/h',
        'reset_password': '100000/h',
        'change_password': '100000/h',
    }
)
class AllauthSignupTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_signup_creates_user_and_redirects(self):
        response = self.client.post(reverse('account_signup'), {
            'email': 'newuser@example.com',
            'password1': 'complexpassword',
            'password2': 'complexpassword',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())


class ApiViewSetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', email='api@local.dev', password='pwd')
        self.author, _ = Author.objects.get_or_create(user=self.user)
        self.news = Post.objects.create(
            author=self.author,
            type=Post.NEWS,
            title='API News',
            text='news text',
        )
        self.article = Post.objects.create(
            author=self.author,
            type=Post.ARTICLE,
            title='API Article',
            text='article text',
        )
        self.client = Client()

    def test_news_api_list_returns_only_news_with_url(self):
        response = self.client.get(reverse('api-news-list'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        items = payload.get('results', payload)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'API News')
        self.assertEqual(items[0]['type'], Post.NEWS)
        self.assertIn('/news/', items[0]['url'])

    def test_article_api_create_binds_type_to_endpoint(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('api-articles-list'),
            data={'title': 'Created via API', 'text': 'body', 'type': Post.NEWS},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        created = Post.objects.get(title='Created via API')
        self.assertEqual(created.type, Post.ARTICLE)
        self.assertEqual(created.author, self.author)


