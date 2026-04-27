@echo off
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
title INSPECTION ENGINE — CLEANUP

echo.
echo  ================================================
echo   INSPECTION ENGINE  ^|  DEPENDENCY CLEANUP
echo  ================================================
echo.
echo  This will DELETE the following heavy directories:
echo.
echo    - venv\              (Python environment + PyTorch ~5-8 GB)
echo    - frontend\node_modules\   (Node.js packages ~200-500 MB)
echo.
echo  The following are SAFE and will NOT be touched:
echo    - All source code  (backend/, frontend/src/)
echo    - Trained model    (runs/.../best.pt)
echo    - Config files     (config.py, requirements.txt)
echo    - Launch scripts   (*.bat)
echo.
set /p CONFIRM="  Type YES to confirm cleanup: "
if /i "%CONFIRM%" NEQ "YES" (
    echo.
    echo  Cancelled. Nothing was deleted.
    pause
    exit /b 0
)

echo.
echo  Removing venv\ ...
if exist "%ROOT%\venv" (
    rmdir /s /q "%ROOT%\venv"
    echo        Done.
) else (
    echo        venv\ not found, skipping.
)

echo  Removing frontend\node_modules\ ...
if exist "%ROOT%\frontend\node_modules" (
    rmdir /s /q "%ROOT%\frontend\node_modules"
    echo        Done.
) else (
    echo        node_modules\ not found, skipping.
)

echo.
echo  ================================================
echo   CLEANUP COMPLETE!
echo.
echo   Disk space has been freed.
echo   Run  INSTALL.bat  to reinstall everything.
echo  ================================================
echo.
pause
endlocal
