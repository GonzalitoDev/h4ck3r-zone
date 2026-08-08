@echo off
title ⚡ NEXUS SURVEILLANCE LOG
cd /d "%~dp0"
setlocal enabledelayedexpansion

set "G=[92m"
set "R=[91m"
set "C=[36m"
set "Y=[93m"
set "P=[95m"
set "W=[97m"
set "D=[90m"
set "X=[0m"

:MENU
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
echo    ║          %W%SURVEILLANCE SYSTEM v1.0%G%                    ║
echo    ║          %D%Logs  •  Commits  •  Deployments%G%              ║
echo    ╚══════════════════════════════════════════════════════╝
echo.
echo %D%═══════════════════════════════════════════════════════
echo    %Y%[1]%X% View Recent Commits     %D%│%X%  %Y%[4]%X% View Changed Files
echo    %Y%[2]%X% View Deploy History     %D%│%X%  %Y%[5]%X% Page Status Check
echo    %Y%[3]%X% View Git Log (Full)     %D%│%X%  %Y%[6]%X% Network Diagnostics
echo                                           %D%│%X%  %Y%[0]%X% Exit
echo %D%═══════════════════════════════════════════════════════
echo.
set /p OPT="%G%root@nexus:~$%X% "

if "%OPT%"=="1" goto COMMITS
if "%OPT%"=="2" goto DEPLOY
if "%OPT%"=="3" goto FULLLOG
if "%OPT%"=="4" goto FILES
if "%OPT%"=="5" goto STATUS
if "%OPT%"=="6" goto NETWORK
if "%OPT%"=="0" goto EXIT
goto MENU

:COMMITS
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%RECENT COMMITS%G%                              ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo %D%   Fetching commit history...%X%
echo.
git log --oneline -15 --pretty=format:"%G%   [%C%%h%G%]%X% %W%%s%X% %D%(%ar)%X%" 2>nul
echo.
echo.
echo %D%═══════════════════════════════════════════════════════
echo.
echo %Y%   Total Commits:%X%
git rev-list --count HEAD 2>nul
echo.
echo %G%   [ENTER]%X% to return to menu
pause >nul
goto MENU

:DEPLOY
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%DEPLOYMENT HISTORY%G%                         ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo %D%   Scanning auto-deploy logs...%X%
echo.
git log --grep="Auto-deploy" --pretty=format:"%G%   [%C%DEPLOY%G%]%X% %D%%ad%X% %Y%▲%X% %W%%s%X%" --date=format:"%%d/%%m %%H:%%M:%%S" -20 2>nul
echo.
echo.
echo %D%═══════════════════════════════════════════════════════
set /a COUNT=0
for /f %%i in ('git log --grep="Auto-deploy" --oneline 2^>nul ^| find /c /v ""') do set COUNT=%%i
echo %Y%   Auto-deploys: !COUNT!%X%
echo %Y%   Last push: %X%
git log -1 --pretty=format:"%G%   %ar%X%" --grep="Auto-deploy" 2>nul
echo.
echo %G%   [ENTER]%X% to return to menu
pause >nul
goto MENU

:FULLLOG
cls
echo.
echo %G%╔══════════════════════════════════════════════════════╗
echo ║         %C%FULL GIT LOG%G%                                 ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo %D%Author          Date              Message%X%
echo %D%────────────── ───────────────── ───────────────────%X%
git log --pretty=format:"%G%%an%X% %D%%ad%X%  %W%%s%X%" --date=short -30 2>nul
echo.
echo.
echo %G%   [ENTER]%X% to return to menu
pause >nul
goto MENU

:FILES
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%LAST CHANGED FILES%G%                         ║
echo   ╚══════════════════════════════════════════════════════╝
echo.
echo %D%   Scanning websecurity-landing...%X%
echo.
for /f "tokens=*" %%f in ('git diff --name-only HEAD~5 HEAD 2^>nul') do (
    echo %G%   [MODIFIED]%X% %W%%%f%X%
)
echo.
echo %D%   Files changed in last 5 commits%X%
echo.
echo %G%   [ENTER]%X% to return to menu
pause >nul
goto MENU

:STATUS
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%PAGE STATUS CHECK%G%                           ║
echo   ╚══════════════════════════════════════════════════════╝
echo.
echo %D%   Checking local status...%X%
echo.
echo %Y%   Branch:%X%
git branch --show-current 2>nul
echo.
echo %Y%   Status:%X%
git status --short websecurity-landing\ 2>nul
echo.
echo %Y%   Last commit:%X%
git log -1 --pretty=format:"%G%   %s%X% %D%(%ar)%X%" 2>nul
echo.
echo.
echo %Y%   Remote URL:%X%
git remote get-url origin 2>nul
echo.
echo %G%   GitHub Pages:%X% https://gonzalitodev.github.io/h4ck3r-zone/websecurity-landing/
echo.
echo %D%═══════════════════════════════════════════════════════
echo %G%   [ENTER]%X% to return to menu
pause >nul
goto MENU

:NETWORK
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%NETWORK DIAGNOSTICS%G%                         ║
echo   ╚══════════════════════════════════════════════════════╝
echo.
echo %D%   Testing connection to GitHub...%X%
echo.
ping -n 2 github.com | find "TTL" >nul
if !errorlevel! equ 0 (
    echo %G%   [OK]%X% GitHub.com reachable
) else (
    echo %R%   [FAIL]%X% Cannot reach GitHub.com
)
echo.
ping -n 2 gonzalitodev.github.io | find "TTL" >nul
if !errorlevel! equ 0 (
    echo %G%   [OK]%X% GitHub Pages reachable
) else (
    echo %R%   [FAIL]%X% Cannot reach GitHub Pages
)
echo.
echo %D%   Local IP:%X%
ipconfig | find "IPv4" 2>nul
echo.
echo %D%   DNS Resolution:%X%
nslookup gonzalitodev.github.io 2>nul | find "Address" | find /v "#"
echo.
echo %G%   [ENTER]%X% to return to menu
pause >nul
goto MENU

:EXIT
cls
echo.
echo %C%   ╔══════════════════════════════════════╗
echo   ║  %G%SESSION TERMINATED%X%                    %C%║
echo   ║  %D%All logs cleared from memory%X%          %C%║
echo   ╚══════════════════════════════════════╝
echo.
timeout /t 2 >nul
exit
