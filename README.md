# NewsPortal

NewsPortal — Django-проект для публикации новостей и статей с авторизацией, категориями, лайками и подписками.

## Что есть в проекте
- Лента новостей и статей
- Роли пользователей (`common`, `authors`)
- Создание/редактирование контента для авторов
- Категории и подписки
- Базовые меры безопасности (CSRF/CSP/CORS middleware)
- Настроенное логирование (`logs/general.log`, `logs/errors.log`, `logs/security.log`)

## Быстрый запуск (локально)
1. Клонировать репозиторий.
2. Создать и активировать виртуальное окружение.
3. Установить зависимости.
4. Создать `.env` из шаблона.
5. Выполнить миграции и запустить сервер.

### Команды
```bash
git clone <repo-url>
cd NewsPortal
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

Создать `.env`:
- Скопировать `.env.example` в `.env`
- При необходимости заполнить значения (БД, почта, OAuth)

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## База данных
По умолчанию используется SQLite (`DB_ENGINE=sqlite`).

Для PostgreSQL:
- поставить `DB_ENGINE=postgres`
- заполнить `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` в `.env`
- выполнить `python manage.py migrate`

## OAuth (опционально)
Google/Yandex вход требует ручной настройки клиентских ключей и callback URL.
Без них проект всё равно запускается и проверяется локально.

## Важно по секретам
- Реальные ключи и пароли в репозиторий не коммитятся.
- Локальные файлы `.env`, логи, кэш, дампы БД и `__pycache__` исключены через `.gitignore`.

