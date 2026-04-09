@echo off
set "PROJECT_ROOT=C:\Users\Devansh Tyagi\Desktop\Projects\Inspection Engine"
title INSPECTION ENGINE MASTER BOOT [V1.2]

echo =======================================================
echo   INITIALIZING INDUSTRIAL AI STACK
echo   LOCATION: %PROJECT_ROOT%
echo =======================================================

:: 1. Launch the Backend + AI Eye
echo [1/3] IGNITING RTX 5060 BACKEND...
start "BACKEND_ENGINE" cmd /k "cd /d %PROJECT_ROOT% && .\venv\Scripts\activate && cd backend && python -m uvicorn app.main:app --reload"

:: 2. Launch the Frontend UI
echo [2/3] STARTING VITE DASHBOARD...
start "FRONTEND_UI" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"

:: 3. Wait for servers to warm up and Auto-Open Browser
echo [3/3] WAITING FOR PORT 5173...
timeout /t 5 /nobreak > nul
echo OPENING DASHBOARD...
start http://localhost:5173

echo.
echo -------------------------------------------------------
echo   SYSTEM DEPLOYED SUCCESSFULLY
echo   UI: http://localhost:5173
echo   API: http://127.0.0.1:8000
echo -------------------------------------------------------
echo.
echo This window will close automatically.
timeout /t 3 > nul
exit
