@echo off
echo ========================================
echo Chemical Equipment Visualizer - Desktop
echo ========================================
echo.

REM Activate venv from parent folder
call "..\.venv\Scripts\activate.bat"

echo [INFO] Launching desktop application...
python main.py

echo.
echo [INFO] Application closed.
pause
