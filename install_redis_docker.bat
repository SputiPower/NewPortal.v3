@echo off
REM Автоматический запуск Redis в Docker на Windows

REM Проверяем, запущен ли Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker не установлен! Установите Docker Desktop с https://www.docker.com/products/docker-desktop
    echo После установки переустартуйте компьютер и запустите этот скрипт снова.
    pause
    exit /b 1
)

REM Проверяем, запущена ли уже Redis контейнер
docker ps | find "redis" >nul 2>&1
if not errorlevel 1 (
    echo Redis уже запущен!
    pause
    exit /b 0
)

REM Удаляем старый контейнер если существует
docker rm -f redis-newsportal >nul 2>&1

REM Запускаем Redis контейнер
echo Запуск Redis контейнера...
docker run -d --name redis-newsportal -p 6379:6379 redis:latest

REM Ждем инициализации
timeout /t 2 /nobreak

REM Проверяем, запустился ли Redis
docker ps | find "redis-newsportal" >nul 2>&1
if errorlevel 1 (
    echo Ошибка при запуске Redis!
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Redis успешно запущен!
    echo URL подключения: redis://localhost:6379/0
    echo.
    echo Используйте в settings.py:
    echo CELERY_BROKER_URL = 'redis://localhost:6379/0'
    echo CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    echo.
)

pause
