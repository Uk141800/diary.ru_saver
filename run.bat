@echo off

python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен. Пожалуйста, установите Python и попробуйте снова.
    echo 1
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден в PATH. Пожалуйста, добавьте Python в PATH и попробуйте снова.
    exit /b 1
)

where pip -V >nul 2>&1
if errorlevel 1 (
    python get-pip.py
)

SET mypath=%~dp0

if not exist "venv" (
    echo Виртуальное окружение не найдено. Создаем новое...
    python -m venv venv
    call /venv/scripts/activate

    if exist "requirements.txt" (
        pip install -r requirements.txt
    ) else (
        echo Файл requirements.txt не найден.
        exit /b 1
    )
) else (
    echo Виртуальное окружение найдено. Активируем...
    call /venv/scripts/activate
)

python main.py
