# NewsPortal

NewsPortal — это веб-приложение на Django для публикации новостей и статей.  
Пользователи могут регистрироваться, входить через e-mail или Yandex, создавать статьи и новости, а также становиться авторами.

---

## Функционал

- Регистрация и вход пользователей  
- Вход через Yandex OAuth  
- Группы пользователей: `common` и `authors`  
- Возможность стать автором  
- Создание и редактирование новостей и статей (только для авторов)  
- Лайки для постов  
- Категории и фильтрация постов  
- Поиск новостей  
- **Асинхронные уведомления** подписчикам о новых постах через Celery  
- **Еженедельный дайджест** с новостями (каждый понедельник в 8:00)  

---

## Установка

1. Клонируем репозиторий:

```bash
git clone https://github.com/SputiPower/NewPortal.v3.git
cd NewPortal.v3
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python manage.py createsuperuser
python manage.py runserver
```

---

## Настройка Redis и Celery

### Установка Redis

#### На Windows:
1. Используйте облачный сервис **Redis Labs** (https://redis.com/try-free/)
2. Или установите Redis локально через WSL (Windows Subsystem for Linux)
3. Или используйте Docker: `docker run -d -p 6379:6379 redis:latest`

#### На macOS/Linux:
```bash
# macOS (через Homebrew)
brew install redis
redis-server

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
redis-server
```

### Запуск Celery Worker и Beat

#### На Windows:
Откройте **две** отдельные командные строки в папке проекта и активируйте виртуальное окружение в каждой.

**Командная строка 1 - Celery Worker:**
```bash
.venv\Scripts\activate
celery -A news worker -l info
```

**Командная строка 2 - Celery Beat (планировщик):**
```bash
.venv\Scripts\activate
celery -A news beat -l info
```

Или используйте подготовленные батники:
```bash
# В одной консоли
run_celery_worker.bat

# В другой консоли
run_celery_beat.bat
```

#### На macOS/Linux:
```bash
# Terminal 1
source .venv/bin/activate
celery -A news worker -l info

# Terminal 2
source .venv/bin/activate
celery -A news beat -l info
```

---

## Функции Celery

### Асинхронная отправка уведомлений
Когда пользователь или админ создаёт новый пост:
- Все подписчики категорий получают письмо с уведомлением
- Письмо отправляется **асинхронно** (не блокируя веб-приложение)
- HTML шаблон находится в `portal/templates/news/email_notification.html`

### Еженедельный дайджест
Каждый **понедельник в 8:00 утра** (UTC):
- Система автоматически собирает все новые посты из избранных категорий пользователя за прошедшую неделю
- Отправляет красиво оформленное письмо с дайджестом
- HTML шаблон находится в `portal/templates/news/email/weekly_digest.html`

---

## Переменные окружения (.env)

Создайте файл `.env` в корне проекта:

```
EMAIL_PROVIDER=gmail
GMAIL_EMAIL_USER=your_email@gmail.com
GMAIL_EMAIL_PASSWORD=your_app_password
```

### Получение App Password для Gmail:
1. Включите 2-фактор аутентификацию на аккаунте Google
2. Перейдите на https://myaccount.google.com/apppasswords
3. Выберите "Mail" и "Windows Computer"
4. Используйте сгенерированный пароль в переменной `GMAIL_EMAIL_PASSWORD`

---

## Структура проекта

```
NewsPortal/
├── news/                           # Конфигурация Django проекта
│   ├── celery.py                  # Конфигурация Celery
│   ├── __init__.py                # Инициализация Celery
│   ├── settings.py                # Настройки Django и Celery
│   └── urls.py
├── portal/                         # Главное приложение
│   ├── models.py                  # Модели (Post, Category, Author...)
│   ├── views.py                   # Представления
│   ├── tasks.py                   # Celery задачи (работа с email)
│   ├── signals.py                 # Django сигналы
│   ├── templates/                 # HTML шаблоны
│   │   └── news/
│   │       ├── email_notification.html    # Email на новый пост
│   │       └── email/
│   │           └── weekly_digest.html     # Email еженедельный дайджест
│   ├── management/
│   │   └── commands/
│   │       └── runapscheduler.py  # APScheduler (альтернатива Celery Beat)
│   └── ...
├── templates/                     # Главные шаблоны
├── static/                        # CSS, JS, images
├── db.sqlite3                     # БД SQLite
├── requirements.txt               # Зависимости Python
├── manage.py                      # Django управления
├── run_celery_worker.bat          # Скрипт для запуска Celery Worker
└── run_celery_beat.bat            # Скрипт для запуска Celery Beat
```

---

## Команды управления

```bash
# Создать суперпользователя
python manage.py createsuperuser

# Применить миграции БД
python manage.py migrate

# Создать миграцию моделей
python manage.py makemigrations

# Запустить тесты
python manage.py test

# Запустить сервер разработки
python manage.py runserver
```

---

## Требования

- Python 3.8+
- Django 6.0+
- Celery 5.3+
- Redis 5.0+
- Pillow (для работы с изображениями)
- django-allauth (для аутентификации Yandex)
- django-filter (для фильтрации постов)

---

## Лицензия

MIT License
