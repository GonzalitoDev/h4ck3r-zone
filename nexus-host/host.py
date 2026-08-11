"""
NEXUS HOST PRO v2.0 — Public 24/7 Web Server
Auto-start with Windows, free public domain via SSH tunnel,
system tray, QR code, dashboard. No signup required.
"""
import os, sys, json, threading, time, socket, http.server, subprocess, re, tempfile
from datetime import datetime
from pathlib import Path
from collections import deque

DATA_DIR = Path.home() / "Documents" / "NexusHost"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "port": 8080,
    "serve_path": "",
    "enable_dashboard": True,
    "dashboard_port": 9999,
    "public_tunnel": True,
    "tunnel_service": "localhost.run",  # or serveo.net
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
    ]:
        if p.exists(): return str(p)
    return ""

config = load_config()
if not config.get("serve_path"):
    config["serve_path"] = find_default_path()
    save_config(config)

http_server = None
dashboard_server = None
tunnel_proc = None
running = False
server_start_time = None
request_log = deque(maxlen=100)
total_requests = 0
public_url = ""
tunnel_connected = False


# ===== SERVERS =====
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
        })

class DashHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global total_requests, public_url, tunnel_connected
        uptime = str(datetime.now() - server_start_time).split(".")[0] if server_start_time else "0:00:00"
        recent = "".join(
            f'<tr><td>{r["time"]}</td><td>{r["ip"]}</td><td>{r["method"]}</td><td>{r["path"]}</td></tr>'
            for r in list(request_log)[-20:]
        )
        pub_html = ""
        if public_url and tunnel_connected:
            pub_html = f'<div class="card" style="background:rgba(52,211,153,0.08);border-color:rgba(52,211,153,0.3)"><span style="color:#34d399;font-weight:700">🌐 Public URL:</span><br><a href="{public_url}" target="_blank" style="color:#818cf8;font-size:16px;text-decoration:none">{public_url}</a><br><span style="font-size:10px;color:#484878">Share this URL — anyone can access your site</span></div>'
        elif config.get("public_tunnel"):
            pub_html = '<div class="card"><span style="color:#fbbf24">⏳ Tunnel connecting...</span><br><span style="font-size:10px;color:#484878">Public URL will appear here</span></div>'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Nexus Host Pro — Dashboard</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a14;color:#d0d0e8;font-family:Segoe UI,sans-serif;padding:20px;max-width:700px;margin:auto}}
h1{{color:#6366f1;font-size:20px;border-bottom:2px solid #1e1e38;padding-bottom:8px;margin-bottom:12px}}
.card{{background:#121225;border:1px solid #1e1e38;border-radius:10px;padding:16px;margin:12px 0}}
.stats{{display:flex;gap:10px;flex-wrap:wrap}}
.stat{{background:#0a0a14;padding:12px 16px;border-radius:8px;text-align:center;border:1px solid #1e1e38;flex:1;min-width:90px}}
.stat .n{{font-size:20px;font-weight:bold;color:#6366f1}}.stat .l{{font-size:8px;color:#484878;text-transform:uppercase;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:10px}}th,td{{padding:4px 8px;border-bottom:1px solid #1e1e38;text-align:left}}
th{{color:#484878;font-size:8px;text-transform:uppercase}}
a{{color:#818cf8}}
</style></head><body>
<h1>⚡ Nexus Host Pro — Dashboard</h1>
{pub_html}
<div class="card"><div class="stats">
<div class="stat"><div class="n">{total_requests}</div><div class="l">Requests</div></div>
<div class="stat"><div class="n">{uptime}</div><div class="l">Uptime</div></div>
<div class="stat"><div class="n">{config["port"]}</div><div class="l">Local Port</div></div>
<div class="stat"><div class="n" style="color:#34d399">ONLINE</div><div class="l">Status</div></div>
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
        sp = config.get("serve_path", "")
        if not sp or not os.path.exists(sp):
            return f"Path not found: {sp}"
        http_server = http.server.HTTPServer(("0.0.0.0", config["port"]), QuietHandler)
        threading.Thread(target=http_server.serve_forever, daemon=True).start()
        if config.get("enable_dashboard"):
            dp = config.get("dashboard_port", 9999)
            dashboard_server = http.server.HTTPServer(("0.0.0.0", dp), DashHandler)
            threading.Thread(target=dashboard_server.serve_forever, daemon=True).start()
        running = True
        server_start_time = datetime.now()
        total_requests = 0
        msg = f"Server started on port {config['port']}"
        if config.get("public_tunnel"):
            threading.Thread(target=start_tunnel, daemon=True).start()
        return msg
    except Exception as e:
        running = False
        return f"Error: {e}"

def stop_servers():
    global http_server, dashboard_server, running, tunnel_proc
    stop_tunnel()
    try:
        if http_server: http_server.shutdown(); http_server = None
        if dashboard_server: dashboard_server.shutdown(); dashboard_server = None
    except: pass
    running = False

# ===== PUBLIC TUNNEL =====
def start_tunnel():
    global tunnel_proc, public_url, tunnel_connected
    while running and config.get("public_tunnel"):
        try:
            if tunnel_proc:
                try: tunnel_proc.terminate()
                except: pass
            port = config["port"]
            # Try localhost.run (more reliable, no banner)
            cmd = (
                f'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 '
                f'-o ConnectTimeout=10 -R 80:localhost:{port} localhost.run'
            )
            tunnel_proc = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Parse the URL from output
            output = b""
            for _ in range(60):
                if not running: break
                try:
                    chunk = tunnel_proc.stdout.read(1)
                    if not chunk: break
                    output += chunk
                    text = output.decode(errors="ignore")
                    m = re.search(r'(https?://[a-zA-Z0-9\-]+\.lhr\.life)', text)
                    if not m:
                        m = re.search(r'(https?://[a-zA-Z0-9\-]+\.serveo\.net)', text)
                    if m:
                        public_url = m.group(1)
                        tunnel_connected = True
                        break
                except: break
            if not public_url and running:
                time.sleep(10)
        except Exception as e:
            print(f"Tunnel error: {e}")
            time.sleep(10)

def stop_tunnel():
    global tunnel_proc, tunnel_connected, public_url
    tunnel_connected = False
    if tunnel_proc:
        try: tunnel_proc.terminate()
        except: pass
        tunnel_proc = None

# ===== AUTO-START =====
def enable_auto_start():
    """Set up Windows auto-start via registry (more reliable than Startup folder)."""
    import winreg
    try:
        exe = sys.argv[0] if getattr(sys, 'frozen', False) else sys.executable
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NexusHostPro", 0, winreg.REG_SZ,
                         f'"{exe}" --silent')
        winreg.CloseKey(key)
        return True, "Auto-start enabled — arranca solo con Windows"
    except Exception as e:
        return False, str(e)

def disable_auto_start():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "NexusHostPro")
        winreg.CloseKey(key)
        return True
    except: return False

def is_auto_start_enabled():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "NexusHostPro")
        winreg.CloseKey(key)
        return True
    except: return False

# ===== GUI =====
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except:
    HAS_TRAY = False


def create_tray():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([3, 3, 29, 29], fill=(99, 102, 241, 255))
    draw.ellipse([10, 10, 22, 22], fill=(10, 10, 20, 255))

    def on_open():
        import webbrowser; webbrowser.open(f"http://localhost:{config['port']}")

    def on_dash():
        import webbrowser; webbrowser.open(f"http://localhost:{config.get('dashboard_port',9999)}")

    def on_pub():
        nonlocal_tunnel_msg()
        if public_url:
            import webbrowser; webbrowser.open(public_url)

    def on_auto():
        if is_auto_start_enabled():
            disable_auto_start()
        else:
            ok, msg = enable_auto_start()

    def on_exit():
        stop_servers()
        try: icon.stop()
        except: pass
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(f"🌐 Open Site (:{config['port']})", on_open),
        pystray.MenuItem(f"📊 Dashboard (:{config.get('dashboard_port',9999)})", on_dash),
        pystray.MenuItem("🔗 Copy Public URL", on_pub),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🚀 Auto-Start: ON" if is_auto_start_enabled() else "🚀 Auto-Start: OFF", on_auto),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Stop & Exit", on_exit),
    )
    icon = pystray.Icon("nexus_host", img, "Nexus Host Pro", menu)
    threading.Thread(target=lambda: (time.sleep(0.3), print(start_servers()), start_tunnel_notify()), daemon=True).start()
    icon.run()


def start_tunnel_notify():
    global public_url
    for _ in range(30):
        if public_url: break
        time.sleep(2)

def nonlocal_tunnel_msg():
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        from tkinter import messagebox
        if public_url:
            r.clipboard_clear(); r.clipboard_append(public_url)
            messagebox.showinfo("Public URL", f"Copied!\n{public_url}")
        else:
            messagebox.showinfo("Tunnel", "Tunnel connecting... Retry in a moment.")
        r.destroy()
    except: pass


def run_gui():
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title("Nexus Host Pro v2.0")
    root.geometry("420x240")
    root.configure(bg="#0a0a14")
    root.resizable(False, False)
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 420) // 2
    y = (root.winfo_screenheight() - 240) // 2
    root.geometry(f"+{x}+{y}")

    tk.Label(root, text="⚡ Nexus Host Pro v2.0", font=("Segoe UI", 14, "bold"),
            fg="#818cf8", bg="#0a0a14").pack(pady=(14, 2))
    tk.Label(root, text="24/7 Web Server + Free Public Domain", font=("Segoe UI", 9),
            fg="#484878", bg="#0a0a14").pack()

    status_lbl = tk.Label(root, text="Starting...", font=("Segoe UI", 9, "bold"),
                          fg="#fbbf24", bg="#0a0a14")
    status_lbl.pack(pady=(6, 2))

    url_var = tk.StringVar(value="Public URL: connecting...")
    url_lbl = tk.Label(root, textvariable=url_var, font=("Consolas", 9),
                       fg="#34d399", bg="#0a0a14", wraplength=380)
    url_lbl.pack()

    info_lbl = tk.Label(root, text=f"Local: http://localhost:{config['port']} | Dashboard: :{config.get('dashboard_port',9999)}",
                        font=("Segoe UI", 8), fg="#484878", bg="#0a0a14")
    info_lbl.pack()

    btn_f = tk.Frame(root, bg="#0a0a14"); btn_f.pack(pady=8)
    auto_var = tk.StringVar(value="🚀 Auto-Start: ON" if is_auto_start_enabled() else "🚀 Auto-Start: OFF")

    def _toggle():
        nonlocal auto_var
        if running:
            stop_servers(); status_lbl.config(text="STOPPED", fg="#f87171")
            btn.config(text="▶ START")
        else:
            msg = start_servers(); status_lbl.config(text="RUNNING", fg="#34d399")
            btn.config(text="⏹ STOP")

    def _auto_toggle():
        if is_auto_start_enabled():
            disable_auto_start(); auto_var.set("🚀 Auto-Start: OFF")
        else:
            enable_auto_start(); auto_var.set("🚀 Auto-Start: ON")

    def _copy_url():
        if public_url:
            root.clipboard_clear(); root.clipboard_append(public_url)
            messagebox.showinfo("Copied", f"Public URL copied!\n{public_url}")

    btn = tk.Button(btn_f, text="▶ START", command=_toggle, font=("Segoe UI", 9),
                    bg="#6366f1", fg="#fff", relief=tk.FLAT, padx=12, pady=4, cursor="hand2")
    btn.pack(side=tk.LEFT, padx=2)

    for text, cmd in [("🌐 Open", lambda: __import__('webbrowser').open(f"http://localhost:{config['port']}")),
                       ("📊 Dash", lambda: __import__('webbrowser').open(f"http://localhost:{config.get('dashboard_port',9999)}")),
                       ("📎 Copy", _copy_url)]:
        tk.Button(btn_f, text=text, command=cmd, font=("Segoe UI", 9),
                 bg="#121225", fg="#d0d0e8", relief=tk.FLAT, padx=8, pady=4,
                 cursor="hand2").pack(side=tk.LEFT, padx=2)

    tk.Button(btn_f, textvariable=auto_var, command=_auto_toggle, font=("Segoe UI", 8),
             bg="#121225", fg="#d0d0e8", relief=tk.FLAT, padx=6, pady=4,
             cursor="hand2").pack(side=tk.LEFT, padx=2)

    tk.Button(btn_f, text="▬ Hide", command=root.withdraw, font=("Segoe UI", 9),
             bg="#121225", fg="#d0d0e8", relief=tk.FLAT, padx=8, pady=4,
             cursor="hand2").pack(side=tk.LEFT, padx=2)

    root.protocol("WM_DELETE_WINDOW", root.withdraw)

    def _update_url():
        if tunnel_connected and public_url:
            url_var.set(f"🌐 {public_url}")
            url_lbl.config(fg="#34d399")
        elif config.get("public_tunnel"):
            url_var.set("⏳ Tunnel connecting... (needs OpenSSH)")
            url_lbl.config(fg="#fbbf24")
        else:
            url_var.set("Public URL: disabled")
            url_lbl.config(fg="#484878")
        if running:
            info_lbl.config(text=f"Local: http://localhost:{config['port']} | Dashboard: :{config.get('dashboard_port',9999)}")
        root.after(3000, _update_url)

    root.after(500, _update_url)
    root.after(800, lambda: (_toggle() if not running else None))
    root.mainloop()


def main():
    # Enable auto-start on first run
    if "--silent" in sys.argv:
        # Running from auto-start — just start servers silently
        config["public_tunnel"] = True
        save_config(config)
        start_servers()
        # Keep alive
        try:
            while True: time.sleep(60)
        except KeyboardInterrupt:
            stop_servers()
        return

    if "--auto-start" in sys.argv or "--setup" in sys.argv:
        ok, msg = enable_auto_start()
        print(msg)
        return

    if not is_auto_start_enabled():
        enable_auto_start()

    if HAS_TRAY:
        create_tray()
    else:
        run_gui()


if __name__ == "__main__":
    main()
