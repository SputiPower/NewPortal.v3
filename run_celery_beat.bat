@echo off
REM скрипт для запуска Celery Beat (планировщик задач) на Windows
cd /d %~dp0
call .venv\Scripts\activate.bat
celery -A news beat -l info
pause
