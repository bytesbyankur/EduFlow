@echo off
echo ========================================
echo   Setting up EduFlow Neural Environment 
echo ========================================

:: 1. Create Virtual Environment
if not exist ".venv" (
    echo [1/4] Creating virtual environment (.venv)...
    python -m venv .venv
) else (
    echo [1/4] Existing .venv detected.
)

:: 2. Activate Environment
echo [2/4] Activating .venv...
call .venv\Scripts\activate.bat

:: 3. Upgrade Pip and Install Dependencies
echo [3/4] Installing dependencies from requirements.txt...
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

:: 4. Database Migrations
echo [4/4] Running database migrations...
if exist "backend\manage.py" (
    python backend\manage.py makemigrations
    python backend\manage.py migrate
) else (
    python manage.py makemigrations
    python manage.py migrate
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo To run the server:
echo   .venv\Scripts\activate
echo   python backend\manage.py runserver
echo ========================================
