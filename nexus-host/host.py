"""
NEXUS HOST PRO v1.0 — 24/7 Background Web Server
System tray mode. Minimizes to tray, never closes. Auto-start with Windows.
Serves static files, dashboard, proxy. Ultra-lightweight.
"""
import os, sys, json, threading, time, socket, http.server, subprocess
from datetime import datetime
from pathlib import Path
from collections import deque

DATA_DIR = Path.home() / "Documents" / "NexusHost"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "port": 80,
    "serve_path": "",
    "auto_start": True,
    "enable_dashboard": True,
    "dashboard_port": 9999,
}

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except:
        return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def find_default_path():
    for p in [
        Path(__file__).resolve().parent.parent / "websecurity-landing",
        Path.home() / "Desktop/Programacion v2/Nexus Bot/websecurity-landing",
        Path.home() / "Documents/NexusBot/websecurity-landing",
    ]:
        if p.exists(): return str(p)
    return ""


config = load_config()
if not config.get("serve_path"):
    config["serve_path"] = find_default_path()
    save_config(config)

http_server = None
dashboard_server = None
running = False
server_start_time = None
request_log = deque(maxlen=100)
total_requests = 0


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=config["serve_path"], **kwargs)

    def log_message(self, format, *args):
        global total_requests
        total_requests += 1
        request_log.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "ip": self.client_address[0],
            "method": self.command,
            "path": self.path[:80],
            "status": 200,
        })

class DashHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = str(datetime.now() - server_start_time).split(".")[0] if server_start_time else "0:00:00"
        recent = "".join(
            f'<tr><td>{r["time"]}</td><td>{r["ip"]}</td><td>{r["method"]}</td><td>{r["path"]}</td></tr>'
            for r in list(request_log)[-20:]
        )
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Nexus Host — Dashboard</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a14;color:#d0d0e8;font-family:Segoe UI,sans-serif;padding:24px;max-width:800px;margin:auto}}
h1{{color:#6366f1;font-size:22px;border-bottom:2px solid #1e1e38;padding-bottom:10px}}
.card{{background:#121225;border:1px solid #1e1e38;border-radius:10px;padding:18px;margin:14px 0}}
.stats{{display:flex;gap:14px;flex-wrap:wrap}}
.stat{{background:#0a0a14;padding:14px 18px;border-radius:8px;text-align:center;border:1px solid #1e1e38;flex:1;min-width:100px}}
.stat .n{{font-size:22px;font-weight:bold;color:#6366f1}}.stat .l{{font-size:9px;color:#484878;text-transform:uppercase;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:10px}}th,td{{padding:5px 8px;border-bottom:1px solid #1e1e38;text-align:left}}
th{{color:#484878;font-size:8px;text-transform:uppercase}}
.green{{color:#34d399;font-weight:bold}}
</style></head><body>
<h1>⚡ Nexus Host Pro — Dashboard</h1>
<div class="card"><div class="stats">
<div class="stat"><div class="n">{total_requests}</div><div class="l">Requests</div></div>
<div class="stat"><div class="n">{uptime}</div><div class="l">Uptime</div></div>
<div class="stat"><div class="n">{config['port']}</div><div class="l">Port</div></div>
<div class="stat"><div class="n" class="green">ONLINE</div><div class="l">Status</div></div>
</div></div>
<div class="card"><h3 style="color:#818cf8;font-size:12px;margin-bottom:8px">Recent Requests</h3>
<table><tr><th>Time</th><th>IP</th><th>Method</th><th>Path</th></tr>{recent}</table></div>
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args): pass


def start_servers():
    global http_server, dashboard_server, running, server_start_time, total_requests
    try:
        serve_path = config.get("serve_path", "")
        if not serve_path or not os.path.exists(serve_path):
            return f"Path not found: {serve_path}"

        http_server = http.server.HTTPServer(("0.0.0.0", config["port"]), QuietHandler)
        threading.Thread(target=http_server.serve_forever, daemon=True).start()

        if config.get("enable_dashboard"):
            dashboard_server = http.server.HTTPServer(("0.0.0.0", config.get("dashboard_port", 9999)), DashHandler)
            threading.Thread(target=dashboard_server.serve_forever, daemon=True).start()

        running = True
        server_start_time = datetime.now()
        total_requests = 0

        msg = (
            f"⚡ Nexus Host Pro STARTED\n"
            f"   Site: http://localhost:{config['port']}\n"
            f"   Dashboard: http://localhost:{config.get('dashboard_port',9999)}\n"
            f"   Serving: {serve_path}\n"
            f"   24/7 mode: active"
        )
        return msg
    except Exception as e:
        running = False
        return f"Error: {e}"


def stop_servers():
    global http_server, dashboard_server, running
    try:
        if http_server: http_server.shutdown(); http_server = None
        if dashboard_server: dashboard_server.shutdown(); dashboard_server = None
    except: pass
    running = False
    return "Server stopped"


# ===== TRY SYSTEM TRAY =====
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except:
    HAS_TRAY = False


def create_tray():
    if not HAS_TRAY:
        return run_headless()

    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([3, 3, 29, 29], fill=(99, 102, 241, 255))
    draw.ellipse([10, 10, 22, 22], fill=(10, 10, 20, 255))

    def on_open(icon):
        import webbrowser
        webbrowser.open(f"http://localhost:{config['port']}")

    def on_dash(icon):
        import webbrowser
        webbrowser.open(f"http://localhost:{config.get('dashboard_port',9999)}")

    def on_folder(icon):
        os.startfile(config.get("serve_path", "."))

    def on_exit(icon):
        stop_servers()
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(f"🌐 Open Site (:{config['port']})", on_open),
        pystray.MenuItem(f"📊 Dashboard (:{config.get('dashboard_port',9999)})", on_dash),
        pystray.MenuItem("📂 Open Folder", on_folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Stop & Exit", on_exit),
    )

    icon = pystray.Icon("nexus_host", img, f"Nexus Host Pro (:{config['port']})", menu)
    threading.Thread(target=lambda: (time.sleep(0.5), print(start_servers())), daemon=True).start()
    icon.run()


def run_headless():
    """Fallback: minimal console with system tray simulation."""
    try:
        import tkinter as tk
    except:
        print(start_servers())
        print("Press Ctrl+C to stop")
        try:
            while True: time.sleep(10)
        except KeyboardInterrupt:
            print(stop_servers())
        return

    root = tk.Tk()
    root.title("Nexus Host Pro")
    root.geometry("380x120")
    root.configure(bg="#0a0a14")
    root.resizable(False, False)
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 380) // 2
    y = (root.winfo_screenheight() - 120) // 2
    root.geometry(f"+{x}+{y}")

    tk.Label(root, text="⚡ Nexus Host Pro", font=("Segoe UI", 13, "bold"),
            fg="#818cf8", bg="#0a0a14").pack(pady=(12, 2))
    status_lbl = tk.Label(root, text="Starting...", font=("Segoe UI", 9), fg="#484878", bg="#0a0a14")
    status_lbl.pack()

    btn_f = tk.Frame(root, bg="#0a0a14"); btn_f.pack(pady=8)

    def _toggle():
        if running:
            stop_servers()
            status_lbl.config(text="STOPPED", fg="#f87171")
            btn.config(text="▶ START")
        else:
            msg = start_servers()
            status_lbl.config(text="RUNNING", fg="#34d399")
            btn.config(text="⏹ STOP")

    btn = tk.Button(btn_f, text="▶ START", command=_toggle, font=("Segoe UI", 9),
                    bg="#6366f1", fg="#fff", relief=tk.FLAT, padx=12, pady=4, cursor="hand2")
    btn.pack(side=tk.LEFT, padx=3)

    tk.Button(btn_f, text="🌐 Open", command=lambda: __import__('webbrowser').open(f"http://localhost:{config['port']}"),
             font=("Segoe UI", 9), bg="#121225", fg="#d0d0e8", relief=tk.FLAT, padx=10, pady=4,
             cursor="hand2").pack(side=tk.LEFT, padx=3)

    tk.Button(btn_f, text="▬ Hide", command=root.withdraw,
             font=("Segoe UI", 9), bg="#121225", fg="#d0d0e8", relief=tk.FLAT, padx=10, pady=4,
             cursor="hand2").pack(side=tk.LEFT, padx=3)

    root.protocol("WM_DELETE_WINDOW", root.withdraw)
    root.after(500, lambda: (_toggle() if not running else None))
    root.mainloop()


def auto_start_setup():
    """Create shortcut in Windows Startup folder."""
    try:
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        from tkinter import messagebox
        startup = os.path.join(os.environ["APPDATA"],
                              "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        exe_path = sys.executable if not getattr(sys, 'frozen', False) else sys.argv[0]
        vbs = f'''
Set WshShell = CreateObject("WScript.Shell")
Set sc = WshShell.CreateShortcut("{startup}\\NexusHost.lnk")
sc.TargetPath = "{exe_path}"
sc.WorkingDirectory = "{os.path.dirname(exe_path)}"
sc.Description = "Nexus Host Pro - 24/7 Web Server"
sc.Save'''
        vbs_path = os.path.join(DATA_DIR, "startup.vbs")
        with open(vbs_path, "w") as f: f.write(vbs)
        subprocess.run(["cscript", "//nologo", vbs_path], capture_output=True)
        os.remove(vbs_path)
        messagebox.showinfo("Auto-Start", "✅ Nexus Host arrancará con Windows.")
        root.destroy()
    except Exception as e:
        print(f"Auto-start error: {e}")


def main():
    if "--auto-start" in sys.argv:
        auto_start_setup()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--auto-start":
        auto_start_setup()
        return

    if HAS_TRAY:
        create_tray()
    else:
        run_headless()


if __name__ == "__main__":
    main()
