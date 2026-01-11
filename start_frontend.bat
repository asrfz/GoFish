@echo off
echo Starting GoFish Frontend...
cd /d "%~dp0\frontend"
call ..\venv\Scripts\activate.bat
npm run dev
pause
