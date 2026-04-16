@echo off
TITLE Ge-mini Public Link Generator 🌐
echo ==========================================
echo    Generando Enlace Publico para Ge-mini
echo ==========================================
echo.
echo NOTA: El servidor principal (start_app.bat) debe estar corriendo.
echo.
npx localtunnel --port 8000
pause
