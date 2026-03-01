# Полная инструкция по запуску News Portal с Celery на Windows

## Шаг 1: Установка зависимостей

```bash
# Активируйте виртуальное окружение
.venv\Scripts\activate

# Установите все зависимости
pip install -r requirements.txt
```

## Шаг 2: Настройка Redis

### Вариант A: Redis в облаке (Redis Labs) - РЕКОМЕНДУЕТСЯ ДЛЯ WINDOWS

1. Перейдите на https://redis.com/try-free/
2. Зарегистрируйтесь или войдите
3. Создайте новую базу данных (Redis database)
4. Скопируйте строку подключения (выглядит как `redis://:password@host:port`)
5. В файле `news/settings.py`, найдите строки:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

6. Замените `localhost:6379` на адрес вашей облачной БД

**Пример:**
```python
CELERY_BROKER_URL = 'redis://:mypassword@redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345/0'
CELERY_RESULT_BACKEND = 'redis://:mypassword@redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345/0'
```

### Вариант B: Redis локально через Docker

1. Установите Docker Desktop с официального сайта
2. Откройте PowerShell и выполните:

```bash
docker run -d -p 6379:6379 redis:latest
```

3. Проверьте, что контейнер запущен:

```bash
docker ps
```

## Шаг 3: Запуск Django приложения

```bash
python manage.py runserver
```

Приложение будет доступно по адресу: http://127.0.0.1:8000/

## Шаг 4: Запуск Celery Worker

**Откройте новую PowerShell окно** (ВАЖНО!) и выполните:

```bash
# Aktivируйте виртуальное окружение
.venv\Scripts\activate

# Запустите Celery Worker
celery -A news worker -l info
```

Вы должны увидеть что-то подобное:
```
[2025-03-01 10:30:45,123: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-03-01 10:30:45,234: INFO/MainProcess] mingle: sync with 3 friends
[2025-03-01 10:30:45,345: INFO/MainProcess] celery worker started
```

## Шаг 5: Запуск Celery Beat (для расписания)

**Откройте ещё одну PowerShell окно** и выполните:

```bash
# Aktivируйте виртуальное окружение
.venv\Scripts\activate

# Запустите Celery Beat
celery -A news beat -l info
```

## Шаг 6: Тестирование

1. Откройте браузер: http://127.0.0.1:8000/
2. Создайте или логинитесь в систему
3. Создайте новый пост/новость
4. **Результат:** Проверьте консоль Celery Worker - там должны быть логи об отправке писем

## Как выглядит работающая система?

### Terminal 1 - Django сервер:
```
[02/Mar/2025 10:30:45] "GET / HTTP/1.1" 200 5432
[02/Mar/2025 10:30:52] "POST /news/create/ HTTP/1.1" 302 0
```

### Terminal 2 - Celery Worker:
```
[2025-03-01 10:30:52,456: INFO/MainProcess] Received task: portal.tasks.send_notification_to_subscribers
[2025-03-01 10:30:53,567: INFO/MainProcess] Task portal.tasks.send_notification_to_subscribers[abc123...] succeeded in 1.234s
```

### Terminal 3 - Celery Beat:
```
[2025-03-01 08:00:00,123: INFO/MainProcess] Executing periodic task: send_weekly_digest
```

## Частые проблемы и решения

### Проблема 1: "Connection refused" при подключении к Redis

**Решение:**
- Убедитесь, что Redis запущен (локально или облако)
- Проверьте строку подключения в `settings.py`
- Убедитесь, что брандмауэр не блокирует порт 6379

### Проблема 2: "Celery worker не видит задачи"

**Решение:**
- Перезагрузите Celery Worker после изменения `tasks.py`
- Убедитесь, что файл `tasks.py` находится в папке `portal/`
- Проверьте что в `portal/__init__.py` импортируются сигналы

### Проблема 3: Письма не отправляются

**Решение:**
- Убедитесь что .env файл настроен правильно
- Проверьте логи Django сервера на ошибки email
- Убедитесь что пользователи имеют валидный email адрес
- Если используете Gmail - используйте App Password, не обычный пароль

### Проблема 4: "RuntimeError: no running event loop"

**Решение:**
- Убедитесь что используете `celery -A news worker`, а не просто `celery worker`
- Перезагрузите Worker процесс

## Проверка что всё работает

### 1. Проверка подключения к Redis:

```bash
python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask
from celery import current_app

# Проверить является ли брокер доступным
print(current_app.connection().as_uri())  # Должен вернуть строку подключения

# Если это сработает без ошибок - всё в порядке
```

### 2. Проверка что задачи выполняются:

В Django shell:

```python
from portal.tasks import send_notification_to_subscribers

# Запустить тестовую задачу
result = send_notification_to_subscribers.delay(1)

# Проверить статус
print(result.status)  # Должен быть 'SUCCESS' через несколько секунд
```

### 3. Создать пост и посмотреть логи:

1. Создайте новый пост через веб-интерфейс
2. Откройте консоли Celery Worker и Beat
3. Вы должны увидеть логи выполнения задач

## Команды управления

```bash
# Просмотр активных задач
celery -A news inspect active

# Просмотр зарегистрированных задач
celery -A news inspect registered

# Просмотр статистики
celery -A news inspect stats

# Завершить всех workers
celery -A news control shutdown
```

## Готowo! 🎉

Ваше приложение News Portal теперь использует:
- ✅ Асинхронную отправку писем об новых постах
- ✅ Еженедельный дайджест каждый понедельник в 8:00
- ✅ Celery для управления асинхронными задачами
- ✅ Redis как message broker и результат бэкенд
