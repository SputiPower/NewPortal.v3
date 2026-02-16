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
