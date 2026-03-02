@echo off
REM скрипт для запуска Celery Worker на Windows
cd /d %~dp0
call .venv\Scripts\activate.bat
celery -A news worker -l info -P solo
pause

