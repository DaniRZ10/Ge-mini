@echo off
TITLE Ge-mini Launcher 💠
echo ==========================================
echo    Lanzando Ge-mini - Proyecto Antigravity
echo ==========================================

:: Abrir el navegador en la URL local
start http://127.0.0.1:8000/static/index.html

:: Ejecutar el servidor usando el interprete del entono virtual
echo Usando interprete: .venv\Scripts\python.exe
echo Presiona Ctrl+C para detener el servidor.
echo.
".venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000
pause
