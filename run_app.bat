@echo off
cd /d %~dp0
venv\Scripts\activate
python app.py
pause