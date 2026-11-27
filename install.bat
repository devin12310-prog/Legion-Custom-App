@echo off
title Legion Custom Installer
echo.
echo  ========================================
echo   Legion Custom App - Installer
echo  ========================================
echo.

:: Create Start Menu shortcut
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT=%STARTMENU%\Legion Custom.lnk"
set "TARGET=%~dp0run.bat"

echo Creating Start Menu shortcut...

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Legion Custom App for Legion Go'; $s.Save()"

echo.
echo Installing Python packages...
python -m pip install -r "%~dp0requirements.txt" --quiet

echo.
echo Done!
echo You can now find "Legion Custom" in your Start Menu.
echo.
pause
