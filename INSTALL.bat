@echo off
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
title INSPECTION ENGINE — INSTALLER

echo.
echo  ================================================
echo   INSPECTION ENGINE  ^|  ONE-CLICK INSTALLER
echo  ================================================
echo.
echo  This will install:
echo    [1] Python virtual environment
echo    [2] PyTorch Nightly (CUDA 12.8 / Blackwell SM 12.0)
echo    [3] Backend Python dependencies
echo    [4] Frontend Node.js dependencies
echo.
echo  Estimated disk usage: ~7-10 GB
echo  Estimated time      : ~5-15 minutes (depends on internet)
echo.
pause

:: -------------------------------------------------------
:: STEP 1 — Python virtual environment
:: -------------------------------------------------------
echo.
echo  [1/4] Creating Python virtual environment...
if exist "%ROOT%\venv" (
    echo        venv already exists, skipping creation.
) else (
    python -m venv "%ROOT%\venv"
    if errorlevel 1 (
        echo  [ERROR] Failed to create venv. Is Python 3.13+ in your PATH?
        pause & exit /b 1
    )
    echo        venv created successfully.
)

:: -------------------------------------------------------
:: STEP 2 — PyTorch Nightly (CUDA 12.8)
:: -------------------------------------------------------
echo.
echo  [2/4] Installing PyTorch Nightly (CUDA 12.8)...
echo        ^(This is ~2-3 GB and may take several minutes^)
"%ROOT%\venv\Scripts\pip.exe" install --pre torch torchvision torchaudio ^
    --index-url https://download.pytorch.org/whl/nightly/cu128
if errorlevel 1 (
    echo  [ERROR] PyTorch installation failed. Check your internet connection.
    pause & exit /b 1
)

:: -------------------------------------------------------
:: STEP 3 — Backend dependencies
:: -------------------------------------------------------
echo.
echo  [3/4] Installing backend dependencies...
"%ROOT%\venv\Scripts\pip.exe" install -r "%ROOT%\backend\requirements.txt"
if errorlevel 1 (
    echo  [ERROR] Backend dependency installation failed.
    pause & exit /b 1
)

:: -------------------------------------------------------
:: STEP 4 — Frontend dependencies
:: -------------------------------------------------------
echo.
echo  [4/4] Installing frontend Node.js packages...
cd /d "%ROOT%\frontend"
call npm install
if errorlevel 1 (
    echo  [ERROR] npm install failed. Is Node.js v18+ installed?
    pause & exit /b 1
)

echo.
echo  ================================================
echo   INSTALLATION COMPLETE!
echo.
echo   Run  Run_Inspection_Engine.bat  to launch.
echo  ================================================
echo.
pause
endlocal
