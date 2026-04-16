@echo off
TITLE Ge-mini Test Runner 🧪
echo ==========================================
echo    Ejecutando Tests - Proyecto Ge-mini
echo ==========================================
echo.

:: Volver a la raíz del proyecto para ejecutar pytest
cd ..

:: Ejecutar tests usando el interprete del entorno virtual
echo Usando interprete: .venv\Scripts\python.exe
echo.
".venv\Scripts\python.exe" -m pytest

echo.
echo ==========================================
echo    Pruebas completadas.
echo ==========================================
pause
