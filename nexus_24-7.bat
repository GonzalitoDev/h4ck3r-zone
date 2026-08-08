@echo off
title ⚡ NEXUS 24/7 — System Monitor
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
echo    ║          %W%24/7 CONTROL CENTER v1.0%G%                   ║
echo    ╚══════════════════════════════════════════════════════╝
echo.
echo %D%═══════════════════════════════════════════════════════
echo    %Y%[1]%X% Start Auto-Deploy        %D%│%X% %Y%[5]%X% Start All Services
echo    %Y%[2]%X% Start Server Pro        %D%│%X% %Y%[6]%X% Stop All Services
echo    %Y%[3]%X% Start VPN               %D%│%X% %Y%[7]%X% Status Check
echo    %Y%[4]%X% Start VPS Monitor       %D%│%X% %Y%[8]%X% Set Auto-Start Windows
echo                                           %D%│%X% %Y%[0]%X% Exit
echo %D%═══════════════════════════════════════════════════════
echo.
echo %Y%   Services Status:%X%
echo    %D%──────────────────────────────────────────%X%
call :CHECK "Auto-Deploy" "auto_deploy.py"
call :CHECK "Nexus Server" "nexus-server\dist\NexusServer.exe"
call :CHECK "Nexus VPN" "nexus-vpn\dist\NexusVPN.exe"
call :CHECK "VPS Monitor" "nexus-vps\dist\NexusVPS.exe"
echo    %D%──────────────────────────────────────────%X%
echo.
set /p OPT="%G%root@nexus:~$%X% "

if "%OPT%"=="1" start "Auto-Deploy" python auto_deploy.py & goto MENU
if "%OPT%"=="2" start "NexusServer" nexus-server\dist\NexusServer.exe & goto MENU
if "%OPT%"=="3" start "NexusVPN" nexus-vpn\dist\NexusVPN.exe & goto MENU
if "%OPT%"=="4" start "NexusVPS" nexus-vps\dist\NexusVPS.exe & goto MENU
if "%OPT%"=="5" goto STARTALL
if "%OPT%"=="6" goto STOPALL
if "%OPT%"=="7" goto STATUS
if "%OPT%"=="8" goto AUTOSTART
if "%OPT%"=="0" exit
goto MENU

:CHECK
if exist "%~2" (
    tasklist /fi "imagename eq %~nx2" 2>nul | find "%~nx2" >nul
    if !errorlevel! equ 0 (
        echo    %G%[RUNNING]%X% %~1
    ) else (
        echo    %D%[STOPPED]%X% %~1
    )
) else (
    echo    %R%[NOT FOUND]%X% %~1
)
goto :eof

:STARTALL
cls
echo.
echo %G%    ╔══════════════════════════════════════════════════════╗
echo    ║         %C%STARTING ALL SERVICES%G%                         ║
echo    ╚══════════════════════════════════════════════════════╝
echo.
echo %G%[>]%X% Starting Auto-Deploy Watcher...
start "Auto-Deploy" python auto_deploy.py
echo %G%[OK]%X% Auto-Deploy started
echo %G%[>]%X% Starting Nexus Server Pro...
if exist "nexus-server\dist\NexusServer.exe" start "NexusServer" nexus-server\dist\NexusServer.exe
echo %G%[OK]%X% Nexus Server started
echo %G%[>]%X% Starting Nexus VPN...
if exist "nexus-vpn\dist\NexusVPN.exe" start "NexusVPN" nexus-vpn\dist\NexusVPN.exe
echo %G%[OK]%X% Nexus VPN started
echo %G%[>]%X% Starting VPS Monitor...
if exist "nexus-vps\dist\NexusVPS.exe" start "NexusVPS" nexus-vps\dist\NexusVPS.exe
echo %G%[OK]%X% VPS Monitor started
echo.
echo %G%[OK]%X% All services launched successfully!
echo %G%[OK]%X% 24/7 mode activated
echo.
echo %D%═══════════════════════════════════════════════════════
echo %Y%  Leave this window open. Services run in background.%X%
echo %D%═══════════════════════════════════════════════════════
echo.
timeout /t 3 >nul
goto MENU

:STOPALL
cls
echo.
echo %R%  Stopping all services...%X%
taskkill /fi "imagename eq python.exe" /f 2>nul >nul
echo %R%  [OK]%X% Python services stopped
taskkill /fi "imagename eq NexusServer.exe" /f 2>nul >nul
echo %R%  [OK]%X% Nexus Server stopped
taskkill /fi "imagename eq NexusVPN.exe" /f 2>nul >nul
echo %R%  [OK]%X% Nexus VPN stopped
taskkill /fi "imagename eq NexusVPS.exe" /f 2>nul >nul
echo %R%  [OK]%X% VPS Monitor stopped
echo %G%[OK]%X% All services stopped
timeout /t 2 >nul
goto MENU

:STATUS
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%SYSTEM STATUS%G%                               ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo %Y%   Running Processes:%X%
echo %D%   ──────────────────────────────────────────%X%
tasklist /fi "imagename eq python.exe" 2>nul | find "python" >nul && echo %G%   [ACTIVE]%X% Auto-Deploy (Python)
tasklist /fi "imagename eq NexusServer.exe" 2>nul | find "Nexus" >nul && echo %G%   [ACTIVE]%X% Nexus Server
tasklist /fi "imagename eq NexusVPN.exe" 2>nul | find "Nexus" >nul && echo %G%   [ACTIVE]%X% Nexus VPN
tasklist /fi "imagename eq NexusVPS.exe" 2>nul | find "Nexus" >nul && echo %G%   [ACTIVE]%X% VPS Monitor
echo %D%   ──────────────────────────────────────────%X%
echo.
echo %Y%   Network:%X%
ping github.com -n 1 >nul 2>&1 && echo %G%   [ONLINE]%X% Internet connection active || echo %R%   [OFFLINE]%X% No internet
echo.
echo %Y%   Uptime:%X%
systeminfo | find "System Boot Time" 2>nul
echo.
echo %G%   [ENTER]%X% to return
pause >nul
goto MENU

:AUTOSTART
cls
echo.
echo %G%   ╔══════════════════════════════════════════════════╗
echo   ║         %C%AUTO-START WITH WINDOWS%G%                    ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo %Y%   Creating startup shortcut...%X%
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS=%TEMP%\nexus_startup.vbs"

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS%"
echo strPath = WshShell.SpecialFolders("Startup") ^& "\Nexus 24-7.lnk" >> "%VBS%"
echo Set oSC = WshShell.CreateShortcut(strPath) >> "%VBS%"
echo oSC.TargetPath = "%~f0" >> "%VBS%"
echo oSC.WorkingDirectory = "%~dp0" >> "%VBS%"
echo oSC.Description = "Nexus 24/7 Control Center" >> "%VBS%"
echo oSC.Save >> "%VBS%"

cscript //nologo "%VBS%" >nul 2>&1
del "%VBS%" >nul 2>&1

echo %G%   [OK]%X% Nexus 24/7 will auto-start with Windows
echo %G%   [OK]%X% Shortcut created in Startup folder
echo.
echo %G%   [ENTER]%X% to return
pause >nul
goto MENU
