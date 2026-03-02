# Perfect World Board (Django)

Проект реализует ТЗ «фанатская доска объявлений для MMORPG Perfect World» на Django.

## Реализовано по ТЗ
1. Регистрация пользователя и подтверждение email одноразовым кодом.
2. Авторизация/выход пользователя.
3. Создание, редактирование, удаление объявлений после входа.
4. Объявление содержит заголовок, категорию и rich-text контент (WYSIWYG-редактор).
5. Категории строго из ТЗ:
   `Танки`, `Хилы`, `ДД`, `Торговцы`, `Гилдмастеры`, `Квестгиверы`, `Кузнецы`, `Кожевники`, `Зельевары`, `Мастера заклинаний`.
6. Отклики на объявления (текстом).
7. Email-уведомления:
   - автору объявления при новом отклике;
   - автору отклика при принятии отклика.
8. Приватная страница владельца объявлений с откликами:
   - фильтр по объявлению;
   - удаление отклика;
   - принятие отклика.
9. Новостная рассылка пользователям через management command.

## Основные URL
- `GET /pw/` — список объявлений (фильтры + поиск)
- `GET /pw/signup/` — регистрация
- `GET /pw/verify-email/` — подтверждение email-кода
- `GET /pw/login/`, `POST /pw/logout/` — вход/выход
- `GET /pw/ads/create/` — создать объявление
- `GET /pw/ads/<id>/` — страница объявления + форма отклика
- `GET /pw/ads/<id>/edit/`, `GET /pw/ads/<id>/delete/` — управление своим объявлением
- `GET /pw/responses/` — приватный кабинет откликов по своим объявлениям
- `POST /pw/responses/<id>/accept/` — принять отклик
- `POST /pw/responses/<id>/delete/` — удалить отклик

## Быстрый запуск
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
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Почта и фоновые задачи
Для email-уведомлений нужны SMTP-переменные в `.env`.

Если используете периодические задачи (рассылки/дайджесты), поднимите Celery:
```bash
celery -A news worker -l info -P solo
celery -A news beat -l info
```

Windows-скрипты:
- `run_celery_worker.bat`
- `run_celery_beat.bat`

## Рассылка пользователям
Команда:
```bash
python manage.py send_pw_newsletter --subject "Perfect World News" --message "Текст рассылки"
```

## Проверка проекта
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Технические примечания
- Заголовок `Perfect World` выводится сразу под шапкой сайта на всех страницах `/pw/...`.
- В проекте сохранен существующий функционал NewsPortal; модуль Perfect World добавлен без разрушения текущей структуры.
- В `.gitignore` исключены локальные и runtime-файлы (`.env`, логи, sqlite wal/shm, celery beat state и пр.).
