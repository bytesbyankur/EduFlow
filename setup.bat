@echo off
echo ========================================
echo   Setting up EduFlow Environment...
echo ========================================

if not exist ".venv" (
    echo [1/4] Creating virtual environment (.venv)...
    python -m venv .venv
) else (
    echo [1/4] Existing .venv detected.
)

echo [2/4] Activating .venv...
call .venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install numpy==1.26.4
pip install -r requirements.txt

echo [4/4] Running database migrations...
if exist "backend" (
    python backend\manage.py makemigrations
    python backend\manage.py migrate
) else (
    python manage.py makemigrations
    python manage.py migrate
)

echo ========================================
echo   Setup Complete!
echo ========================================
echo To start the server:
echo   .venv\Scripts\activate
echo   python backend\manage.py runserver
echo ========================================
pause
