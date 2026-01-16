# portal/populate_db.py

"""
Скрипт для наполнения базы данных NewsPortal тестовыми данными.

Выполняет все пункты ТЗ:
1. Создает пользователей и авторов.
2. Создает категории.
3. Создает статьи и новости.
4. Присваивает категории постам.
5. Создает комментарии.
6. Применяет like() и dislike().
7. Обновляет рейтинги авторов.
8. Выводит лучшего пользователя и его рейтинг.
9. Выводит лучшую статью и комментарии к ней.
"""

from django.contrib.auth.models import User
from portal.models import Author, Category, Post, Comment

def run():
    # 1 Создать пользователей
    user1 = User.objects.create_user(username='ivan')
    user2 = User.objects.create_user(username='petr')

    # 2
    #Создать авторов
    author1 = Author.objects.create(user=user1)
    author2 = Author.objects.create(user=user2)

    # 3 Создать категории
    sport, _ = Category.objects.get_or_create(name='Спорт')
    politics, _ = Category.objects.get_or_create(name='Политика')
    education, _ = Category.objects.get_or_create(name='Образование')
    it, _ = Category.objects.get_or_create(name='IT')

    # 4 Создать посты (2 статьи + 1 новость)
    post1 = Post.objects.create(author=author1, type='AR', title='Django ORM', text='Подробная статья про Django ORM. ' * 10)
    post2 = Post.objects.create(author=author2, type='AR', title='Python Basics', text='Статья про основы Python. ' * 10)
    post3 = Post.objects.create(author=author1, type='NE', title='Новости IT', text='Свежие новости из мира IT.')

    # 5 Присвоить категории постам
    post1.categories.add(sport, it)
    post2.categories.add(education)
    post3.categories.add(it)

    # 6 Создать комментарии
    comment1 = Comment.objects.create(post=post1, user=user2, text='Отличная статья!')
    comment2 = Comment.objects.create(post=post1, user=user1, text='Спасибо за отзыв!')
    comment3 = Comment.objects.create(post=post2, user=user1, text='Полезный материал')
    comment4 = Comment.objects.create(post=post3, user=user2, text='Интересная новость')

    # 7 Применить like() и dislike() к постам и комментариям
    post1.like()
    post1.like()
    post2.dislike()
    post3.like()

    comment1.like()
    comment1.like()
    comment2.dislike()
    comment3.like()
    comment4.like()

    # 8 Обновить рейтинги авторов
    author1.update_rating()
    author2.update_rating()

    # 9 Вывести лучшего пользователя
    best_author = Author.objects.order_by('-rating').first()
    print(f'Лучший пользователь: {best_author.user.username}, рейтинг: {best_author.rating}')

    # 10 Вывести лучшую статью
    best_post = Post.objects.order_by('-rating').first()
    print(f'''
Лучшая статья:
Дата: {best_post.created_at}
Автор: {best_post.author.user.username}
Рейтинг: {best_post.rating}
Заголовок: {best_post.title}
Превью: {best_post.preview()}
''')

    # 11 Вывести все комментарии к этой статье
    comments = Comment.objects.filter(post=best_post)
    for c in comments:
        print(f'{c.created_at} | {c.user.username} | {c.rating} | {c.text}')


#  Чтобы запустить:
# python manage.py shell
# >>> from portal.populate_db import run
# >>> run()
