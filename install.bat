@echo off
title Ge-mini -- Instalador

:: -- Auto-elevacion de privilegios de administrador --------------------------
:: Si ya somos admin, continuar. Si no, relanzar pidiendo UAC.
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo  [!!] Este instalador necesita permisos de administrador para instalar Ollama.
    echo       Se va a pedir confirmacion ahora mismo...
    echo.
    timeout /t 3 /nobreak >nul
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: -- Lanzar el instalador PowerShell ----------------------------------------
powershell -NoProfile -ExecutionPolicy ByPass -File "%~dp0tools\_setup\install.ps1" -ProjectRoot "%~dp0."
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] La instalacion ha fallado con codigo %ERRORLEVEL%.
    echo Revisa los mensajes anteriores para mas detalles.
    pause
)
