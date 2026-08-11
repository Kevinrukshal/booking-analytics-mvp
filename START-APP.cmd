@echo off
setlocal
cd /d "%~dp0"
title Booking Analytics - Start

docker info >nul 2>&1
if errorlevel 1 (
  echo Open Docker Desktop and wait until Docker is running, then try again.
  pause
  exit /b 1
)

docker compose up -d
if errorlevel 1 (
  echo Could not start Booking Analytics.
  pause
  exit /b 1
)

start "" "http://localhost:5173"
echo Booking Analytics is running at http://localhost:5173
timeout /t 3 >nul
