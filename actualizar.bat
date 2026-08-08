@echo off
title Nexus Auto-Deploy
cd /d "%~dp0"

echo.
echo ============================================
echo    NEXUS AUTO-DEPLOY
echo    Vigila cambios y pushea a GitHub
echo ============================================
echo.
echo Modo: AUTOMATICO
echo Cada vez que guardes un archivo en la pagina,
echo se sube solo a GitHub en 5 segundos.
echo.
echo No cierres esta ventana. Dejala abierta.
echo Para detener: Ctrl+C o cerra la ventana.
echo ============================================
echo.

python auto_deploy.py

pause
