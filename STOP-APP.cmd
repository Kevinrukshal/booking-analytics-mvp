@echo off
setlocal
cd /d "%~dp0"
title Booking Analytics - Stop

docker compose down
if errorlevel 1 (
  echo Could not stop Booking Analytics. Make sure Docker Desktop is running.
  pause
  exit /b 1
)

echo Booking Analytics stopped. Your database volume was preserved.
pause
