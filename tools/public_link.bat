@echo off
TITLE Ge-mini Public Link Generator 🌐
echo ==========================================
echo    Generando Enlace Publico para Ge-mini
echo ==========================================
echo.

:: Ir a la raíz del proyecto (una carpeta arriba de donde está este script)
cd /d "%~dp0.."
echo NOTA: El servidor principal (start_app.bat) debe estar corriendo.
echo.
npx localtunnel --port 8000
pause
