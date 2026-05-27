@echo off
title Ge-mini — Instalador
powershell -NoProfile -ExecutionPolicy ByPass -File "%~dp0tools\_setup\install.ps1" -ProjectRoot "%~dp0."
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] La instalacion ha fallado con codigo %ERRORLEVEL%.
    echo Revisa los mensajes anteriores para mas detalles.
    pause
)
