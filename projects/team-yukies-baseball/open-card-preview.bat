@echo off
setlocal
cd /d "%~dp0"

set "PORT=8765"
set "BUILD=20260927v3"
set "URL=http://127.0.0.1:%PORT%/card-template-html/?build=%BUILD%"

where py >nul 2>&1
if %errorlevel%==0 (
  start "TEAM YUKIES Card Server" cmd /k "cd /d ""%~dp0"" && py -m http.server %PORT% --bind 127.0.0.1"
  timeout /t 1 /nobreak >nul
  start "" "%URL%"
  exit /b 0
)

where python >nul 2>&1
if %errorlevel%==0 (
  start "TEAM YUKIES Card Server" cmd /k "cd /d ""%~dp0"" && python -m http.server %PORT% --bind 127.0.0.1"
  timeout /t 1 /nobreak >nul
  start "" "%URL%"
  exit /b 0
)

echo Python launcher was not found.
echo.
echo Install Python or run this folder with another local HTTP server,
echo then open:
echo %URL%
pause
exit /b 1
