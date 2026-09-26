@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\build-launcher.ps1"
if errorlevel 1 (
  echo.
  echo Launcher build failed.
  pause
  exit /b 1
)
echo.
echo Team Yukies Card Preview.exe updated.
pause
