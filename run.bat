@echo off
cd /d "%~dp0"
python main.py %*
if errorlevel 1 (
    echo.
    echo Python failed to start. Make sure Python is installed and in PATH.
    pause
)
