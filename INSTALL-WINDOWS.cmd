@echo off
setlocal
cd /d "%~dp0"
title Booking Analytics - First-time setup

echo.
echo ==================================================
echo   Booking Analytics - Windows setup
echo ==================================================
echo.

where docker >nul 2>&1
if errorlevel 1 goto docker_missing

docker info >nul 2>&1
if errorlevel 1 goto docker_not_running

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created local .env from safe defaults.
) else (
  echo Existing .env preserved.
)

echo Checking configuration...
docker compose config --quiet
if errorlevel 1 goto setup_failed

echo Building and starting the application...
echo The first build can take several minutes.
docker compose up --build -d
if errorlevel 1 goto setup_failed

echo.
echo Setup complete. Opening Booking Analytics...
start "" "http://localhost:5173"
echo.
echo Use START-APP.cmd next time you want to start the app.
echo Use STOP-APP.cmd when you want to stop it.
pause
exit /b 0

:docker_missing
echo Docker Desktop is not installed or is not available in PATH.
echo Install it from: https://www.docker.com/products/docker-desktop/
echo Restart Windows after installation, open Docker Desktop, then run this file again.
pause
exit /b 1

:docker_not_running
echo Docker Desktop is installed but is not running yet.
echo Open Docker Desktop, wait until it says Docker is running, then run this file again.
pause
exit /b 1

:setup_failed
echo.
echo Setup did not complete. Review the error shown above.
echo You can run this installer again after fixing the problem.
pause
exit /b 1
