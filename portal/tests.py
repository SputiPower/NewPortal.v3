from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core import mail

from .models import Category, Author, Post


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


class EmailNotificationTests(TestCase):
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

    def test_news_creation_sends_email(self):
        url = reverse('news_create')
        data = {
            'title': 'Заголовок',
            'text': 'Текст новости очень длинный, чтобы получился предварительный фрагмент.',
            'type': 'NW',
            'categories': [self.category.pk],
        }
        response = self.client.post(url, data)
        # one email should be sent to anna (sent from Post.save only)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.subject, 'Заголовок')
        self.assertIn('Здравствуй, anna', sent.body)
        self.assertIn('<h2>Заголовок</h2>', sent.alternatives[0][0])
        self.assertIn('Текст новости очень длинный', sent.alternatives[0][0])

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
            })
            self.assertEqual(response.status_code, 302)
        # fourth attempt should fail and display error
        response = self.client.post(url, {
            'title': 'Fourth',
            'text': 'text',
            'type': 'NW',
            'categories': [self.category.pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вы уже опубликовали 3 новости за последние 24 часа')
        self.assertEqual(Post.objects.filter(author__user=self.user, type='NW').count(), 3)


class AllauthSignupTests(TestCase):
    def test_confirmation_email_sent(self):
        # make sure signup page works and sends email
        response = self.client.post(reverse('account_signup'), {
            'email': 'newuser@example.com',
            'password1': 'complexpassword',
            'password2': 'complexpassword',
        })
        # a redirect should occur after form submission
        self.assertEqual(response.status_code, 302)
        # check that email was queued
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('newuser@example.com', email.to)
        # subject from custom template
        self.assertIn('подтверждение регистрации', email.subject.lower())
        # body should contain confirmation link
        body = email.body or ''
        self.assertIn('confirm-email', body)


