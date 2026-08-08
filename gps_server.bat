@echo off
title Nexus GPS - Local Server
cd /d "%~dp0"
echo.
echo   📡 Iniciando servidor local Nexus GPS...
echo   Abri en tu navegador: http://localhost:8000
echo   Presiona Ctrl+C para detener
echo.
python -m http.server 8000 --directory nexus-gps
pause
