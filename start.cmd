@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Please run setup.ps1 first to install dependencies.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false
pause
