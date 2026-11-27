@echo off
setlocal EnableDelayedExpansion
title Legion Custom - Installer
cd /d "%~dp0"

echo.
echo  ============================================
echo       LEGION CUSTOM  -  INSTALLER
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found!
    echo  Install Python from Microsoft Store or python.org
    echo  Make sure "Add to PATH" is checked.
    echo.
    pause
    exit /b 1
)

echo  [1/4] Installing Python packages...
python -m pip install -r requirements.txt --quiet --upgrade
echo        Done.

echo  [2/4] Creating Start Menu shortcut...
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SM_SHORTCUT=%STARTMENU%\Legion Custom.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SM_SHORTCUT%'); ^
   $s.TargetPath = '%~dp0run.bat'; ^
   $s.WorkingDirectory = '%~dp0'; ^
   $s.WindowStyle = 7; ^
   $s.Description = 'Legion Custom App'; ^
   $s.Save()"
echo        Start Menu: Legion Custom

echo  [3/4] Creating Desktop shortcut...
set "DESKTOP=%USERPROFILE%\Desktop"
set "DESK_SHORTCUT=%DESKTOP%\Legion Custom.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%DESK_SHORTCUT%'); ^
   $s.TargetPath = '%~dp0run.bat'; ^
   $s.WorkingDirectory = '%~dp0'; ^
   $s.WindowStyle = 7; ^
   $s.Description = 'Legion Custom App'; ^
   $s.Save()"
echo        Desktop: Legion Custom

echo  [4/4] Launching app...
echo.
echo  ============================================
echo   Install complete!
echo   - Start Menu shortcut created
echo   - Desktop shortcut created
echo  ============================================
echo.

start "" "%~dp0run.bat"

timeout /t 2 >nul
exit /b 0
