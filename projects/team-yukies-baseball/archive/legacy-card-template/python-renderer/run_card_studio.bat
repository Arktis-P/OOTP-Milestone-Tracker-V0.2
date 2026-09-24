@echo off
setlocal
cd /d "%~dp0\..\.."
python projects\team-yukkies-baseball\card_studio.py %*
endlocal
