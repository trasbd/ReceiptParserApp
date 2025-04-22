@echo off
cd /d %~dp0
.\venv\Scripts\Activate.ps1
python app.py
pause