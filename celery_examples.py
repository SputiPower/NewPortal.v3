"""
Примеры использования асинхронных задач Celery в News Portal

Для тестирования этих примеров:
1. Убедитесь, что Redis запущен
2. Запустите Celery Worker: celery -A news worker -l info
3. Запустите Celery Beat: celery -A news beat -l info (для расписания)
4. Откройте Django shell: python manage.py shell
5. Импортируйте функции и вызывайте их
"""

from portal.models import Post, Category, Author
from portal.tasks import (
    send_notification_to_subscribers,
    send_post_notification_email,
    send_weekly_digest,
    send_digest_email,
)
from django.contrib.auth.models import User

# ===============================================================================
# ПРИМЕР 1: Отправка уведомления о новом посте подписчикам
# ===============================================================================

def example_1_send_notification():
    """
    Отправляет уведомление о посте всем подписчикам из его категорий
    """
    # Получаем пост (для примера используем первый пост)
    post = Post.objects.first()
    
    if post:
        # Метод 1: Использование delay() - самый простой способ
        send_notification_to_subscribers.delay(post.id)
        print(f"✅ Асинхронное уведомление отправлено для поста '{post.title}'")
        
        # Метод 2: Использование apply_async() с дополнительными параметрами
        # send_notification_to_subscribers.apply_async(
        #     args=[post.id],
        #     countdown=60  # Задержка на 60 секунд
        # )


# ===============================================================================
# ПРИМЕР 2: Отправка письма конкретному пользователю о конкретном посте
# ===============================================================================

def example_2_send_single_email():
    """
    Отправляет письмо одному пользователю о одном посте
    """
    # Получаем пост и пользователя
    post = Post.objects.first()
    user = User.objects.filter(email__isnull=False).first()
    
    if post and user:
        # Опция 1: Использование delay()
        send_post_notification_email.delay(post.id, user.id)
        print(f"✅ Письмо отправлено пользователю {user.email}")
        
        # Опция 2: С задержкой в 30 секунд
        # send_post_notification_email.apply_async(
        #     args=[post.id, user.id],
        #     countdown=30
        # )


# ===============================================================================
# ПРИМЕР 3: Запуск еженедельного дайджеста вручную
# ===============================================================================

def example_3_send_weekly_digest_manually():
    """
    Отправляет еженедельный дайджест всем подписанным пользователям
    (обычно это запускается автоматически по расписанию)
    """
    # Вызов основной задачи
    send_weekly_digest.delay()
    print("✅ Еженедельный дайджест отправлен всем подписчикам")


# ===============================================================================
# ПРИМЕР 4: Отправка дайджеста конкретному пользователю
# ===============================================================================

def example_4_send_digest_to_user():
    """
    Отправляет дайджест конкретному пользователю
    """
    from django.utils import timezone
    from datetime import timedelta
    
    user = User.objects.filter(email__isnull=False).first()
    
    if user:
        one_week_ago = timezone.now() - timedelta(days=7)
        send_digest_email.delay(user.id, one_week_ago.isoformat())
        print(f"✅ Дайджест отправлен пользователю {user.email}")


# ===============================================================================
# ПРИМЕР 5: Проверка статуса задачи
# ===============================================================================

def example_5_check_task_status():
    """
    Проверить статус выполнения асинхронной задачи
    """
    post = Post.objects.first()
    
    if post:
        # Вызовем задачу и сохраним её ID
        task = send_notification_to_subscribers.delay(post.id)
        task_id = task.id
        print(f"🔍 Task ID: {task_id}")
        print(f"🔍 Task Status: {task.status}")
        # Доступные статусы: PENDING, STARTED, RETRY, FAILURE, SUCCESS
        
        # Получить результат (если есть)
        if task.ready():
            result = task.result
            print(f"✅ Результат: {result}")
        else:
            print("⏳ Задача всё ещё выполняется...")


# ===============================================================================
# ПРИМЕР 6: Использование apply_async() с параметрами
# ===============================================================================

def example_6_apply_async_options():
    """
    Использование применить_async с различными опциями
    """
    post = Post.objects.first()
    
    if post:
        # Вариант 1: Задержка на 60 секунд
        send_notification_to_subscribers.apply_async(
            args=[post.id],
            countdown=60  # секунды
        )
        print("⏳ Задача отложена на 60 секунд")
        
        # Вариант 2: Максимальное количество попыток при ошибке
        send_notification_to_subscribers.apply_async(
            args=[post.id],
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0.1,  # начальная задержка между попытками
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        print("🔄 Задача добавлена с автоматическими повторами при ошибке")


# ===============================================================================
# ПРИМЕР 7: Запуск множества задач (цепочка)
# ===============================================================================

def example_7_chain_tasks():
    """
    Выполнять задачи по порядку (одна за другой)
    """
    from celery import chain
    
    post = Post.objects.first()
    users = User.objects.filter(email__isnull=False)[:3]
    
    if post and users:
        # Создаём цепочку: отправим письмо каждому пользователю по очереди
        task_chain = chain([
            send_post_notification_email.s(post.id, user.id)
            for user in users
        ])
        
        result = task_chain.apply_async()
        print(f"✅ Цепочка задач запущена (ID: {result.id})")


# ===============================================================================
# ПРИМЕР 8: Параллельное выполнение задач
# ===============================================================================

def example_8_parallel_tasks():
    """
    Выполнять несколько задач одновременно
    """
    from celery import group
    
    post = Post.objects.first()
    users = User.objects.filter(email__isnull=False)[:5]
    
    if post and users:
        # Создаём группу: все письма отправляются параллельно
        task_group = group([
            send_post_notification_email.s(post.id, user.id)
            for user in users
        ])
        
        result = task_group.apply_async()
        print(f"✅ Группа из {len(list(users))} параллельных задач запущена")


# ===============================================================================
# ЗАПУСК ПРИМЕРОВ
# ===============================================================================

if __name__ == "__main__":
    import django
    django.setup()
    
    print("="*70)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ CELERY В NEWS PORTAL")
    print("="*70)
    print()
    
    # Раскомментируйте нужный пример:
    # example_1_send_notification()
    # example_2_send_single_email()
    # example_3_send_weekly_digest_manually()
    # example_4_send_digest_to_user()
    # example_5_check_task_status()
    # example_6_apply_async_options()
    # example_7_chain_tasks()
    # example_8_parallel_tasks()
