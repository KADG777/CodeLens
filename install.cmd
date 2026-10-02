@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 (
    echo Installation failed. See the message above.
    pause
    exit /b 1
)
echo Ready. Double-click start.cmd to launch.
pause
