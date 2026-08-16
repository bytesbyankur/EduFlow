#!/usr/bin/env bash
set -e

echo "========================================"
echo "  Setting up EduFlow Environment...     "
echo "========================================"

# 1. Create Virtual Environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "[1/4] Existing .venv detected."
fi

# 2. Activate Environment
echo "[2/4] Activating .venv..."
source .venv/bin/activate

# 3. Upgrade Pip & Install Dependencies
echo "[3/4] Installing dependencies from requirements.txt..."
pip install --upgrade pip setuptools wheel
pip install numpy==1.26.4
pip install -r requirements.txt

# 4. Database Migrations
echo "[4/4] Running database migrations..."
if [ -d "backend" ]; then
    python backend/manage.py makemigrations
    python backend/manage.py migrate
else
    python manage.py makemigrations
    python manage.py migrate
fi

echo ""
echo "========================================"
echo "  Setup Complete!                       "
echo "========================================"
echo "To run the server:"
echo "  source .venv/bin/activate"
echo "  python backend/manage.py runserver"
echo "========================================"
