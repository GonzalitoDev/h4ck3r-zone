"""
NEXUS SERVER PRO v2.0 — Ultra-Light Background Server + Proxy
System tray mode, <30MB RAM usage, 24/7 operation.
Static file server, reverse proxy, CORS proxy, admin dashboard.
"""
import os, sys, json, threading, time, socket, urllib.parse, urllib.request
import http.server, ssl, io
from datetime import datetime
from pathlib import Path
from collections import deque

# Lightweight tray or headless — defer heavy tkinter imports
DATA_DIR = Path.home() / "Documents" / "NexusServer"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "web_port": 8080, "proxy_port": 9000,
    "serve_path": "", "proxy_enabled": True,
    "cors_enabled": True, "tray_mode": True,
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
    possible = [
        Path.home() / "Documents" / "Nexus Bot" / "websecurity-landing",
        Path(__file__).resolve().parent.parent / "websecurity-landing",
        Path(__file__).resolve().parent.parent.parent / "websecurity-landing",
    ]
    for p in possible:
        if p.exists(): return str(p)
    return ""


# ===== PROXY SERVER =====
class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self._proxy("GET")
    def do_POST(self): self._proxy("POST")
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _proxy(self, method):
        try:
            url = self.path
            if url == "/":
                self._dashboard(); return
            if url.startswith("/"):
                url = urllib.parse.unquote(url[1:])
            if not url.startswith("http"):
                self.send_error(400); return

            body = self.rfile.read(int(self.headers.get("Content-Length", 0))) if self.headers.get("Content-Length") else None
            req = urllib.request.Request(url, data=body, method=method)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "connection"):
                    req.add_header(k, v)

            resp = urllib.request.urlopen(req, timeout=12)
            self.send_response(resp.status)
            if self.server._cors:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "*")
                self.send_header("Access-Control-Allow-Headers", "*")
            for k, v in resp.headers.items():
                if k.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(k, v)
            self.end_headers()
            data = resp.read()
            self.wfile.write(data)
            self.server._reqs += 1
            self.server._log.append((datetime.now().strftime("%H:%M:%S"), url[:60], resp.status))
            if len(self.server._log) > 50:
                self.server._log.popleft()

        except Exception as e:
            self.send_error(502, str(e)[:100])

    def _dashboard(self):
        s = self.server
        recent = "".join(
            f'<tr><td>{r[0]}</td><td style="color:{"#34d399" if r[2]<400 else "#fbbf24"}">{r[2]}</td><td>{r[1][:50]}</td></tr>'
            for r in list(s._log)[-15:]
        )
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Nexus Server Pro</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#05080f;color:#d0d4e8;font-family:Segoe UI,sans-serif;padding:20px;max-width:700px;margin:auto}}
h1{{color:#38bdf8;font-size:20px;border-bottom:2px solid #1a2560;padding-bottom:8px;margin-bottom:12px}}
.card{{background:#0f1830;border:1px solid #1a2560;border-radius:8px;padding:16px;margin:12px 0}}
.stats{{display:flex;gap:12px;flex-wrap:wrap}}
.stat{{background:#0b1220;padding:12px 16px;border-radius:6px;border:1px solid #1a2560;text-align:center}}
.stat .n{{font-size:20px;font-weight:bold;color:#38bdf8}}.stat .l{{font-size:9px;color:#4a5580;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:10px}}th,td{{padding:4px 8px;border-bottom:1px solid #1a2560}}
th{{color:#4a5580;font-size:8px;text-transform:uppercase;text-align:left}}
</style></head><body>
<h1>⚡ Nexus Server Pro</h1>
<div class="card"><div class="stats">
<div class="stat"><div class="n">{s._reqs}</div><div class="l">Requests</div></div>
<div class="stat"><div class="n">{s._web_port}</div><div class="l">Web</div></div>
<div class="stat"><div class="n">{s._proxy_port}</div><div class="l">Proxy</div></div>
<div class="stat"><div class="n" style="color:#34d399">ONLINE</div><div class="l">Status</div></div>
</div></div>
<div class="card"><h3 style="color:#7dd3fc;font-size:12px;margin-bottom:8px">Recent Requests</h3>
<table><tr><th>Time</th><th>Status</th><th>URL</th></tr>{recent}</table></div>
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


class ProxyServer(http.server.HTTPServer):
    allow_reuse_address = True
    def __init__(self, addr, handler, cors=True, web_port=8080, proxy_port=9000):
        super().__init__(addr, handler)
        self._cors = cors; self._web_port = web_port; self._proxy_port = proxy_port
        self._reqs = 0; self._log = deque(maxlen=50)
        self._start = datetime.now()


# ===== MAIN LOGIC (no GUI dependency until needed) =====
config = load_config()
web_srv = None
proxy_srv = None
running = False


def start_servers(cfg=None):
    global web_srv, proxy_srv, running, config
    if cfg: config = cfg
    if running: return "Already running"

    try:
        # Proxy
        proxy_srv = ProxyServer(("0.0.0.0", config["proxy_port"]), ProxyHandler,
                                cors=config.get("cors_enabled", True),
                                web_port=config["web_port"],
                                proxy_port=config["proxy_port"])
        threading.Thread(target=proxy_srv.serve_forever, daemon=True).start()

        # Web server
        serve_path = config.get("serve_path", "") or find_default_path()
        if serve_path and os.path.exists(serve_path):
            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *a, **kw): super().__init__(*a, directory=serve_path, **kw)
                def log_message(self, *a): pass
            web_srv = http.server.HTTPServer(("0.0.0.0", config["web_port"]), Handler)
            threading.Thread(target=web_srv.serve_forever, daemon=True).start()
            config["serve_path"] = serve_path
            save_config(config)

        running = True
        msg = f"SERVIDOR INICIADO\nWeb: http://localhost:{config['web_port']}\nProxy: http://localhost:{config['proxy_port']}"
        print(msg)
        return msg
    except Exception as e:
        running = False
        err = f"Error: {e}"
        print(err)
        return err


def stop_servers():
    global web_srv, proxy_srv, running
    try:
        if proxy_srv: proxy_srv.shutdown(); proxy_srv = None
        if web_srv: web_srv.shutdown(); web_srv = None
    except: pass
    running = False
    return "Servidor detenido"


# ===== TRY SYSTEM TRAY =====
HAS_PYSTRAY = False
HAS_TK = False

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    pass

try:
    import tkinter as tk
    from tkinter import messagebox, filedialog
    HAS_TK = True
except ImportError:
    pass


def create_tray():
    """Create a minimal system tray icon with menu."""
    if not HAS_PYSTRAY:
        if HAS_TK:
            return _tk_fallback()
        return

    # Create a simple 32x32 icon
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 28, 28], fill=(56, 189, 248, 255))
    draw.ellipse([10, 10, 22, 22], fill=(5, 8, 15, 255))

    def on_start(icon):
        icon.visible = True
        start_servers()

    def on_stop(icon):
        stop_servers()

    def on_exit(icon):
        stop_servers()
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("▶ Start", lambda: start_servers(), enabled=lambda item: not running),
        pystray.MenuItem("⏹ Stop", lambda: stop_servers(), enabled=lambda item: running),
        pystray.MenuItem("🌐 Dashboard", lambda: __import__('webbrowser').open(f"http://localhost:{config['proxy_port']}")),
        pystray.MenuItem("📂 Change Folder", _change_folder_tray),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Exit", on_exit),
    )

    icon = pystray.Icon("nexus_server", img, f"Nexus Server Pro (:{config['proxy_port']})", menu)

    # Auto-start on launch
    threading.Thread(target=lambda: (time.sleep(1), start_servers()), daemon=True).start()
    icon.run()


def _change_folder_tray():
    if HAS_TK:
        root = tk.Tk(); root.withdraw()
        p = filedialog.askdirectory(title="Select folder to serve")
        root.destroy()
        if p:
            config["serve_path"] = p
            save_config(config)
            stop_servers()
            start_servers()


def _tk_fallback():
    """Minimal tkinter GUI - hidden by default, tray-like."""
    root = tk.Tk()
    root.title("Nexus Server Pro")
    root.geometry("400x150")
    root.configure(bg="#05080f")

    tk.Label(root, text="⚡ Nexus Server Pro", font=("Segoe UI", 13, "bold"),
            fg="#38bdf8", bg="#05080f").pack(pady=(16, 4))

    status_lbl = tk.Label(root, text="STOPPED", font=("Segoe UI", 10, "bold"), fg="#f87171", bg="#05080f")
    status_lbl.pack()

    btn_frame = tk.Frame(root, bg="#05080f"); btn_frame.pack(pady=10)

    def toggle():
        if running:
            stop_servers()
            status_lbl.config(text="STOPPED", fg="#f87171")
            btn.config(text="▶ START", bg="#34d399")
        else:
            msg = start_servers()
            status_lbl.config(text="RUNNING", fg="#34d399")
            btn.config(text="⏹ STOP", bg="#f87171")

    btn = tk.Button(btn_frame, text="▶ START", command=toggle, font=("Segoe UI", 10),
                    bg="#34d399", fg="#000", relief=tk.FLAT, padx=16, pady=4, cursor="hand2")
    btn.pack(side=tk.LEFT, padx=4)

    tk.Button(btn_frame, text="🌐 Dashboard", command=lambda: __import__('webbrowser').open(
        f"http://localhost:{config['proxy_port']}"),
             font=("Segoe UI", 9), bg="#0f1830", fg="#d0d4e8", relief=tk.FLAT,
             padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

    tk.Button(btn_frame, text="📂 Folder", command=lambda: _change_folder_tray(),
             font=("Segoe UI", 9), bg="#0f1830", fg="#d0d4e8", relief=tk.FLAT,
             padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

    root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw() if running else root.destroy())
    # Auto-start
    root.after(500, lambda: (toggle() if not running else None))
    root.mainloop()


def main():
    if "--headless" in sys.argv or "--tray" in sys.argv:
        if HAS_PYSTRAY:
            create_tray()
        elif HAS_TK:
            _tk_fallback()
        else:
            # Pure headless - just print
            print(start_servers())
            print("Press Ctrl+C to stop")
            try:
                while True: time.sleep(10)
            except KeyboardInterrupt:
                print(stop_servers())
    else:
        if HAS_PYSTRAY:
            create_tray()
        elif HAS_TK:
            _tk_fallback()
        else:
            print(start_servers())
            try:
                while True: time.sleep(10)
            except KeyboardInterrupt:
                print(stop_servers())


if __name__ == "__main__":
    main()
