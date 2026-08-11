"""
NEXUS HEALTH MONITOR v1.0 — 24/7 Service Watchdog
Auto-detects crashes, restarts services, monitors health.
Keeps all Nexus services alive. Run: python health_check.py
"""
import os, sys, time, subprocess, threading, json, socket, psutil
from datetime import datetime
from pathlib import Path

G = "\033[92m"; R = "\033[91m"; C = "\033[96m"; Y = "\033[93m"
D = "\033[90m"; W = "\033[97m"; X = "\033[0m"

BASE = Path(__file__).resolve().parent

SERVICES = [
    {"name": "Auto-Deploy", "exe": ["python", "auto_deploy.py"], "restart": True},
    {"name": "Nexus Host", "exe": ["nexus-host/dist/NexusHost.exe", "--silent"], "restart": True},
    {"name": "Nexus Server", "exe": ["nexus-server/dist/NexusServer.exe"], "restart": False},
    {"name": "Nexus VPN", "exe": ["nexus-vpn/dist/NexusVPN.exe"], "restart": False},
]

crashes = 0
start_time = datetime.now()


def check_service(svc):
    """Check if a service process is running by looking for its exe name."""
    exe_name = Path(svc["exe"][0]).name.lower()
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            if proc.info["name"] and exe_name in proc.info["name"].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def start_service(svc):
    """Start a service process."""
    global crashes
    exe_path = str(BASE / svc["exe"][0]) if not os.path.isabs(svc["exe"][0]) else svc["exe"][0]

    if not os.path.exists(exe_path):
        print(f"  {R}[MISSING]{X} {svc['name']} — {D}{exe_path}{X}")
        return False

    if check_service(svc):
        print(f"  {D}[OK]{X} {svc['name']} — already running")
        return True

    try:
        args = [exe_path] + svc["exe"][1:]
        if exe_path.endswith(".py"):
            args = ["python", exe_path] + svc["exe"][1:]
        subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
        print(f"  {G}[STARTED]{X} {svc['name']}")
        return True
    except Exception as e:
        print(f"  {R}[FAILED]{X} {svc['name']} — {e}")
        crashes += 1
        return False


def stop_service(svc):
    """Stop a service process."""
    exe_name = Path(svc["exe"][0]).name.lower()
    stopped = False
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"] and exe_name in proc.info["name"].lower():
                proc.terminate()
                stopped = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if stopped:
        print(f"  {R}[STOPPED]{X} {svc['name']}")
    else:
        print(f"  {D}[OK]{X} {svc['name']} — not running")
    return stopped


def status_all():
    """Show status of all services."""
    print(f"\n{Y}  STATUS {datetime.now():%H:%M:%S}{X}")
    print(f"  {D}{'─'*40}{X}")
    running = 0
    for svc in SERVICES:
        if check_service(svc):
            print(f"  {G}[RUNNING]{X} {svc['name']}")
            running += 1
        else:
            print(f"  {R}[DOWN]{X}    {svc['name']}")
    print(f"  {D}{'─'*40}{X}")
    print(f"  {Y}Active: {G}{running}{Y}/{len(SERVICES)}  |  Restarts: {crashes}  |  Uptime: {str(datetime.now()-start_time).split('.')[0]}{X}\n")


def watchdog():
    """Watchdog mode — monitor and auto-restart crashed services."""
    global crashes
    print(f"\n{G}  ╔{'═'*40}╗")
    print(f"  ║     {C}WATCHDOG MODE ACTIVE{G}                  ║")
    print(f"  ╚{'═'*40}╝{X}\n")
    print(f"  {Y}Auto-restart: ON  |  Check interval: 30s{X}")
    print(f"  {D}Press Ctrl+C to stop{X}\n")

    # Start all services
    for svc in SERVICES:
        start_service(svc)

    status_all()

    try:
        while True:
            time.sleep(30)
            for svc in SERVICES:
                if svc.get("restart") and not check_service(svc):
                    print(f"  {Y}[!]{X} {svc['name']} crashed — restarting...")
                    crashes += 1
                    start_service(svc)
            status_all()
    except KeyboardInterrupt:
        print(f"\n  {R}[✗]{X} Watchdog stopped. Total restarts: {crashes}")


def auto_start_setup():
    """Set up Windows auto-start via registry."""
    import winreg
    try:
        exe = sys.executable
        script = str(BASE / "health_check.py")
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NexusHealthMonitor", 0, winreg.REG_SZ,
                         f'"{exe}" "{script}" --watchdog')
        winreg.CloseKey(key)
        print(f"{G}  [OK]{X} Auto-start enabled. Health monitor runs at boot.")
    except Exception as e:
        print(f"{R}  [ERR]{X} {e}")


def main():
    if "--watchdog" in sys.argv:
        watchdog()
    elif "--status" in sys.argv:
        status_all()
    elif "--start" in sys.argv:
        print(f"\n{G}  Starting all services...{X}")
        for svc in SERVICES: start_service(svc)
        status_all()
    elif "--stop" in sys.argv:
        print(f"\n{R}  Stopping all services...{X}")
        for svc in SERVICES: stop_service(svc)
    elif "--setup" in sys.argv:
        auto_start_setup()
    else:
        print(f"\n{G}  NEXUS HEALTH MONITOR v1.0{X}")
        print(f"  {D}── ── ── ── ── ── ── ── ── ──{X}")
        print(f"  {C}python health_check.py --watchdog{X}  — Auto-restart on crash mode")
        print(f"  {C}python health_check.py --start{X}     — Start all services")
        print(f"  {C}python health_check.py --stop{X}      — Stop all services")
        print(f"  {C}python health_check.py --status{X}    — Show status")
        print(f"  {C}python health_check.py --setup{X}     — Auto-start with Windows")
        print()

        status_all()

if __name__ == "__main__":
    main()
