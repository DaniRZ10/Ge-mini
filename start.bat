@echo off
title Ge-mini — Arranque rapido
echo.
echo   [**] Ge-mini -- Arrancando...
echo.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo   [!!] Entorno no encontrado. Ejecuta primero install.bat
    pause & exit /b 1
)
where ollama >nul 2>&1
if %ERRORLEVEL% equ 0 (
    powershell -NoProfile -Command "try { Invoke-RestMethod http://localhost:11434/api/tags -TimeoutSec 2 | Out-Null } catch { Start-Process ollama -ArgumentList serve -WindowStyle Hidden; Start-Sleep 3 }"
)
start http://127.0.0.1:8000/static/index.html
echo   [OK] Servidor en http://127.0.0.1:8000/static/index.html
echo        Presiona Ctrl+C para detener.
echo.
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
exit
