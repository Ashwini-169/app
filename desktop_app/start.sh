#!/bin/bash
# Quick start script for desktop app (Linux/Mac)

echo "========================================"
echo "Chemical Equipment Visualizer - Desktop"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please create it first:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "[INFO] Checking dependencies..."
python -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] PyQt5 not found! Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies!"
        exit 1
    fi
fi

# Check if backend is running
echo "[INFO] Checking backend connection..."
curl -s http://localhost:8002/api/history/ > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] Backend not responding!"
    echo "Please start Django backend first:"
    echo "   cd ../django_backend"
    echo "   python manage.py runserver 8002"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Launch application
echo ""
echo "[INFO] Launching desktop application..."
echo ""
python main.py

# Handle exit
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Application exited with error code $?"
fi

echo ""
echo "[INFO] Application closed."
