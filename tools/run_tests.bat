@echo off
TITLE Ge-mini Test Runner 🧪
echo ==========================================
echo    Ejecutando Tests - Proyecto Ge-mini
echo ==========================================
echo.

:: Ir a la raíz del proyecto (una carpeta arriba de donde está este script)
cd /d "%~dp0.."

:: Ejecutar tests usando el interprete del entorno virtual
echo Usando interprete: .venv\Scripts\python.exe
echo.
".venv\Scripts\python.exe" -m pytest

echo.
echo ==========================================
echo    Pruebas completadas.
echo ==========================================
pause
