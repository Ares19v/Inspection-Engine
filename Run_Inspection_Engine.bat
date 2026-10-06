@echo off
set "PROJECT_ROOT=%~dp0"
title INSPECTION ENGINE MASTER BOOT [V1.2]

echo =======================================================
echo   INITIALIZING INDUSTRIAL AI STACK
echo   LOCATION: %PROJECT_ROOT%
echo =======================================================

set "ACT_CMD="
if exist "%PROJECT_ROOT%venv\Scripts\activate.bat" set "ACT_CMD=.\venv\Scripts\activate && "

:: 1. Launch the Backend + AI Eye
echo [1/3] IGNITING BACKEND...
start "BACKEND_ENGINE" cmd /k "cd /d "%PROJECT_ROOT:~0,-1%" && %ACT_CMD%cd backend && python -m uvicorn app.main:app --port 38192"

:: 2. Launch the Frontend UI
echo [2/3] STARTING VITE DASHBOARD...
start "FRONTEND_UI" cmd /k "cd /d "%PROJECT_ROOT:~0,-1%\frontend" && npm run dev -- --port 38193"

:: 3. Auto-Open Browser
echo [3/3] OPENING DASHBOARD...
timeout /t 1 /nobreak >nul 2>&1 || ping -n 2 127.0.0.1 >nul
start http://localhost:38193

echo.
echo -------------------------------------------------------
echo   SYSTEM DEPLOYED SUCCESSFULLY
echo   UI: http://localhost:38193
echo   API: http://127.0.0.1:38192
echo -------------------------------------------------------
exit
