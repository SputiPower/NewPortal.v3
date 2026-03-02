# Переход NewsPortal на PostgreSQL (Windows)

## 1) Установить PostgreSQL
1. Скачай установщик с официального сайта PostgreSQL.
2. Установи сервер (порт обычно `5432`), запомни пароль пользователя `postgres`.
3. Проверь вход:

```powershell
psql -U postgres -h 127.0.0.1 -p 5432
```

## 2) Создать БД для проекта
В `psql`:

```sql
CREATE DATABASE newsportal;
```

## 3) Установить драйвер в проект
В проект уже добавлен пакет `psycopg2-binary` в `requirements.txt`.
Установить зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4) Переключить `.env` на PostgreSQL
Измени переменные:

```env
DB_ENGINE=postgres
DB_NAME=newsportal
DB_USER=postgres
DB_PASSWORD=ВАШ_ПАРОЛЬ
DB_HOST=127.0.0.1
DB_PORT=5432
```

## 5) Перенести данные из SQLite в PostgreSQL
Пока `DB_ENGINE=sqlite`, сделай дамп:

```powershell
.\.venv\Scripts\python.exe manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 > data.json
```

Переключи `.env` на `DB_ENGINE=postgres`, затем:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py loaddata data.json
```

## 6) Проверка
```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```
