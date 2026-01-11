@echo off
echo Starting GoFish Backend...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python app.py
pause
