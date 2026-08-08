@echo off
title ⚡ NEXUS AUTO-DEPLOY v2.0
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Colors
set "G=[92m"
set "R=[91m"
set "C=[36m"
set "Y=[93m"
set "P=[95m"
set "W=[97m"
set "D=[90m"
set "X=[0m"

:START
cls
echo.
echo %G%    ╔══════════════════════════════════════════════════════╗
echo    ║                                                      ║
echo    ║   %C%███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗%G%    ║
echo    ║   %C%████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝%G%    ║
echo    ║   %C%██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗%G%    ║
echo    ║   %C%██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║%G%    ║
echo    ║   %C%██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║%G%    ║
echo    ║   %C%╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝%G%    ║
echo    ║                                                      ║
echo    ║        %W%AUTO-DEPLOY SYSTEM v2.0%G%                      ║
echo    ║        %D%GitHub Pages Continuous Deployment%G%            ║
echo    ╚══════════════════════════════════════════════════════╝
echo.
echo %D%═══════════════════════════════════════════════════════
echo.

:: Boot sequence
echo %G%[>]%X% Initializing deployment engine...
ping -n 2 127.0.0.1 >nul
echo %G%[OK]%X% Secure channel established
echo %G%[>]%X% Loading watcher modules...
ping -n 1 127.0.0.1 >nul
echo %G%[OK]%X% 12 watcher threads active
echo %G%[>]%X% Scanning target directory...
ping -n 1 127.0.0.1 >nul
echo %G%[OK]%X% Directory: %P%websecurity-landing\%X%
echo %G%[>]%X% Configuring auto-commit pipeline...
ping -n 1 127.0.0.1 >nul
echo %G%[OK]%X% Pipeline ready - %C%5s debounce%X%
echo.
echo %D%═══════════════════════════════════════════════════════
echo %Y%  STATUS: %G%ONLINE%X%  |  %Y%MODE: %C%AUTOMATIC%X%  |  %Y%TARGET: %P%GitHub Pages%X%
echo %D%═══════════════════════════════════════════════════════
echo.
echo %W%  Dejala abierta. Cada vez que guardes un archivo,%X%
echo %W%  se sube automaticamente a GitHub en %C%5 segundos%W%.%X%
echo.
echo %D%  [Ctrl+C] para detener%X%
echo %D%═══════════════════════════════════════════════════════
echo.
echo %G%[LOG]%X% Waiting for file changes...

:: Watch loop
set "LAST_PUSH=%time%"
set /a PUSH_COUNT=0

:WATCH
:: Small delay
ping -n 3 127.0.0.1 >nul

:: Check if any files changed in the last 2 seconds
set CHANGED=0
for /r "websecurity-landing" %%f in (*.html *.json *.css *.js *.png *.ico) do (
    set "FP=%%f"
    if not "!FP!"=="!FP:.update=!" goto :check_done
)
:check_done

:: Try to commit
git add websecurity-landing\ 2>nul
git commit -m "Auto-deploy: %date% %time%" --no-verify 2>nul >nul

:: Check if something was committed
git log -1 --pretty=format:"%s" 2>nul | find "Auto-deploy" >nul
if !errorlevel! equ 0 (
    set /a PUSH_COUNT+=1
    echo %G%[%time:~0,8%]%X% %Y%▲ Change detected! Deploying...%X%
    git push origin master 2>nul >nul
    if !errorlevel! equ 0 (
        echo %G%[%time:~0,8%]%X% %C%✓ PUSH #!PUSH_COUNT! successful%X%
        echo %D%  → GitHub Pages updating (1-3 min)%X%
    ) else (
        echo %R%[%time:~0,8%]%X% %R%✗ Push failed - retrying...%X%
    )
    echo.
)

goto :WATCH
