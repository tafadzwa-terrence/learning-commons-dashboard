@echo off
title Learning Commons Dashboard

:: Start the web server in the background
start /min "" python "%~dp0server.py"

:: Wait 2 seconds for server to start
timeout /t 2 /nobreak >nul

:: Launch Chrome in kiosk mode (fullscreen, no UI chrome)
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --kiosk ^
  --mute-audio ^
  --disable-infobars ^
  --disable-session-crashed-bubble ^
  --autoplay-policy=no-user-gesture-required ^
  http://localhost:8080

exit
