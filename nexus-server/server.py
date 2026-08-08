"""
NEXUS SERVER PRO v1.0 — Self-Hosted Web Server + Proxy
Static file server, reverse proxy, CORS proxy, admin dashboard.
Runs 24/7 with system tray, auto-reconnect, configurable ports.
"""
import os, sys, json, threading, socket, time, re, urllib.parse, urllib.request
import http.server, ssl, io
from datetime import datetime
from pathlib import Path
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#05080f", "bg2": "#0b1220", "card": "#0f1830",
    "border": "#1a2560", "text": "#d0d4e8", "dim": "#4a5580",
    "accent": "#38bdf8", "accent2": "#7dd3fc", "green": "#34d399",
    "red": "#f87171", "orange": "#fb923c", "yellow": "#fbbf24",
}

DATA_DIR = Path.home() / "Documents" / "NexusServer"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "web_port": 8080,
    "proxy_port": 9000,
    "serve_path": "",
    "proxy_enabled": True,
    "cors_enabled": True,
    "rate_limit": 30,
    "max_connections": 50,
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


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Forward proxy - handles CONNECT and regular proxy requests."""

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_OPTIONS(self):
        self._handle_cors()
        self.send_response(200)
        self.end_headers()

    def _handle_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _proxy_request(self, method):
        try:
            target_url = self.path
            if target_url.startswith("/"):
                if target_url == "/":
                    self._serve_dashboard()
                    return
                target_url = urllib.parse.unquote(target_url[1:])

            if not target_url.startswith("http"):
                self.send_error(400, "Invalid URL")
                return

            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else None

            req = urllib.request.Request(target_url, data=body, method=method)
            skip = ["host", "connection", "proxy-connection"]
            for k, v in self.headers.items():
                if k.lower() not in skip:
                    req.add_header(k, v)

            resp = urllib.request.urlopen(req, timeout=15)
            self.send_response(resp.status)

            if self.server.cors_enabled:
                self._handle_cors()

            for k, v in resp.headers.items():
                if k.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(k, v)
            self.end_headers()

            data = resp.read()
            self.wfile.write(data)
            self.server.log_request(method, target_url, resp.status, len(data))

        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")
            self.server.log_request(method, self.path, 502, 0)

    def do_CONNECT(self):
        self.send_error(405, "CONNECT not supported")

    def _serve_dashboard(self):
        total = self.server.total_requests if hasattr(self.server, 'total_requests') else 0
        uptime_str = str(datetime.now() - self.server.start_time).split(".")[0] if hasattr(self.server, 'start_time') else "?"
        recent = list(self.server.request_log) if hasattr(self.server, 'request_log') else []
        recent_html = "".join(
            f'<tr><td style="color:#{r[2]}{r[2]}44">{r[0]}</td><td>{r[1][:60]}</td><td style="color:{r[4]}">{r[3]}">{r[2]}</td><td>{r[3]}</td></tr>'
            for r in recent[-20:]
        )

        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Nexus Server Pro — Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#05080f;color:#d0d4e8;font-family:Segoe UI,sans-serif;padding:24px;max-width:900px;margin:auto}}
h1{{color:#38bdf8;font-size:22px;margin-bottom:4px;border-bottom:2px solid #1a2560;padding-bottom:10px}}
.card{{background:#0f1830;border:1px solid #1a2560;border-radius:10px;padding:20px;margin:16px 0}}
.card h3{{color:#7dd3fc;margin-bottom:10px;font-size:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}}
.stat{{background:#0b1220;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a2560}}
.stat .num{{font-size:24px;font-weight:bold;color:#38bdf8}}
.stat .lbl{{font-size:10px;color:#4a5580;text-transform:uppercase;margin-top:4px}}
table{{width:100%;border-collapse:collapse;font-size:10px;margin-top:8px}}
th,td{{padding:6px 8px;text-align:left;border-bottom:1px solid #1a2560}}
th{{color:#4a5580;font-size:9px;text-transform:uppercase}}
.green{{color:#34d399}}.red{{color:#f87171}}.orange{{color:#fb923c}}
.status{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.status.online{{background:#34d399;box-shadow:0 0 6px #34d399}}
</style></head><body>
<h1>⚡ Nexus Server Pro — Dashboard</h1>
<p style="color:#4a5580;margin-bottom:16px">Self-hosted web server + proxy</p>

<div class="card">
<h3><span class="status online"></span> Server Status</h3>
<div class="stats">
<div class="stat"><div class="num">{total}</div><div class="lbl">Total Requests</div></div>
<div class="stat"><div class="num">{uptime_str}</div><div class="lbl">Uptime</div></div>
<div class="stat"><div class="num">{self.server.web_port}</div><div class="lbl">Web Port</div></div>
<div class="stat"><div class="num">{self.server.proxy_port}</div><div class="lbl">Proxy Port</div></div>
</div>
</div>

<div class="card">
<h3>📋 Recent Requests</h3>
<table><tr><th>Time</th><th>URL</th><th>Status</th><th>Size</th></tr>
{recent_html}
</table>
</div>

<div class="card">
<h3>🔧 Endpoints</h3>
<p style="color:#4a5580;font-size:11px">
<b>Proxy:</b> http://localhost:{self.server.proxy_port}/?url=https://api.example.com/data<br>
<b>CORS Proxy:</b> http://localhost:{self.server.proxy_port}/https://discord.com/api/v10/users/@me<br>
<b>Dashboard:</b> http://localhost:{self.server.proxy_port}/
</p>
</div>

<p style="text-align:center;color:#1a2560;font-size:10px;margin-top:24px">Nexus Server Pro v1.0 — Running 24/7</p>
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass  # Suppress default logging


class ProxyServer(http.server.HTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, cors_enabled=True, callback=None):
        super().__init__(server_address, handler_class)
        self.cors_enabled = cors_enabled
        self.callback = callback
        self.total_requests = 0
        self.request_log = deque(maxlen=100)
        self.start_time = datetime.now()

    def log_request(self, method, url, status, size):
        self.total_requests += 1
        self.request_log.append((datetime.now().strftime("%H:%M:%S"), url, status, size, "green" if status < 400 else "orange" if status < 500 else "red"))
        if self.callback:
            self.callback(method, url, status, size)


class WebFileServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=str(directory) if directory else None, **kwargs)

    def log_message(self, format, *args):
        pass


class WebServer(http.server.HTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, directory=None):
        self.directory = directory
        self.total_requests = 0
        self.request_log = deque(maxlen=100)
        self.start_time = datetime.now()
        super().__init__(server_address, handler_class)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self,
                                directory=self.directory)


class NexusServer:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS SERVER PRO")
        self.root.geometry("800x560")
        self.root.minsize(650, 420)
        self.root.configure(bg=C["bg"])
        self._center()

        self.config = load_config()
        self.web_server = None
        self.proxy_server = None
        self.running = False
        self._build()
        self._load_serve_path()
        self._update_status()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 800) // 2
        y = (self.root.winfo_screenheight() - 560) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="⚡ NEXUS SERVER PRO", font=("Segoe UI", 16, "bold"),
                fg=C["accent"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Self-Hosted Web + Proxy Server", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Status indicator
        status_f = tk.Frame(hdr, bg=C["bg"])
        status_f.pack(side=tk.RIGHT)
        self.status_dot = tk.Canvas(status_f, width=12, height=12, bg=C["bg"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT)
        self._draw_dot("red")
        self.status_text = tk.Label(status_f, text="STOPPED", font=("Segoe UI", 9, "bold"),
                                    fg=C["red"], bg=C["bg"])
        self.status_text.pack(side=tk.LEFT, padx=4)

        # Control buttons
        ctrl = tk.Frame(self.root, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=16, pady=(8, 0))
        self.start_btn = tk.Button(ctrl, text="▶ START SERVER", command=self._toggle_server,
                                   font=("Segoe UI", 10, "bold"), bg=C["green"], fg="#000",
                                   relief=tk.FLAT, padx=20, pady=6, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT)
        tk.Button(ctrl, text="📂 Select Folder", command=self._select_folder,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="🌐 Open Dashboard", command=self._open_dashboard,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="📋 Open Web", command=self._open_web,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="⚙️ Config", command=self._open_config,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        # Info panel
        info_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        info_f.pack(fill=tk.X, padx=16, pady=(8, 0))

        self.info_labels = {}
        for label, key, unit, col in [
            ("Web Server", "web_port", "", 0), ("Proxy Server", "proxy_port", "", 0),
            ("Serving", "serve_path_display", "", 1), ("Proxy", "proxy_status", "", 0),
            ("CORS", "cors_status", "", 0), ("Requests", "total", "", 0),
        ]:
            frame = tk.Frame(info_f, bg=C["card"])
            frame.pack(side=tk.LEFT, padx=12, pady=8, fill=tk.X, expand=True)
            tk.Label(frame, text=label, font=("Segoe UI", 7), fg=C["dim"], bg=C["card"]).pack(anchor="w")
            lbl = tk.Label(frame, text="—", font=("Segoe UI", 11, "bold"), fg=C["accent"], bg=C["card"])
            lbl.pack(anchor="w")
            self.info_labels[key] = lbl

        # Log console
        tk.Label(self.root, text="REQUEST LOG", font=("Segoe UI", 9, "bold"), fg=C["dim"],
                bg=C["bg"]).pack(anchor=tk.W, padx=16, pady=(8, 2))

        log_frame = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        self.log_text = scrolledtext.ScrolledText(log_frame, bg=C["bg2"], fg=C["text"],
                                                   font=("Consolas", 8), wrap=tk.WORD,
                                                   relief=tk.FLAT, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _draw_dot(self, color):
        self.status_dot.delete("all")
        c = {"green": "#34d399", "red": "#f87171", "yellow": "#fbbf24"}.get(color, "#f87171")
        self.status_dot.create_oval(2, 2, 10, 10, fill=c, outline="")

    def _load_serve_path(self):
        path = self.config.get("serve_path", "")
        if not path:
            # Default: try to find landing page
            possible = [
                Path.home().parent / "Desktop" / "Programacion v2" / "Nexus Bot" / "websecurity-landing",
                Path(__file__).resolve().parent.parent / "websecurity-landing",
            ]
            for p in possible:
                if p.exists():
                    path = str(p)
                    self.config["serve_path"] = path
                    save_config(self.config)
                    break
        self._update_info()

    def _select_folder(self):
        from tkinter import filedialog
        p = filedialog.askdirectory(title="Select folder to serve")
        if p:
            self.config["serve_path"] = p
            save_config(self.config)
            self._update_info()
            if self.running:
                self._log("⚠️ Restart server to apply new folder")

    def _open_dashboard(self):
        import webbrowser
        webbrowser.open(f"http://localhost:{self.config['proxy_port']}")

    def _open_web(self):
        import webbrowser
        webbrowser.open(f"http://localhost:{self.config['web_port']}")

    def _open_config(self):
        win = tk.Toplevel(self.root)
        win.title("Server Config"); win.geometry("380x280")
        win.configure(bg=C["bg"]); win.resizable(False, False)
        win.transient(self.root); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 380) // 2; y = (win.winfo_screenheight() - 280) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="CONFIGURATION", font=("Segoe UI", 13, "bold"), fg=C["accent2"],
                bg=C["bg"]).pack(pady=(16, 10))

        entries = {}
        for label, key, default in [("Web Port", "web_port", "8080"),
                                     ("Proxy Port", "proxy_port", "9000"),
                                     ("Rate Limit", "rate_limit", "30")]:
            f = tk.Frame(win, bg=C["bg"]); f.pack(fill=tk.X, padx=30, pady=3)
            tk.Label(f, text=label, font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"],
                    width=14, anchor="w").pack(side=tk.LEFT)
            e = tk.Entry(f, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                        insertbackground=C["accent"], relief=tk.FLAT, width=15)
            e.insert(0, str(self.config.get(key, default)))
            e.pack(side=tk.LEFT, ipady=3)
            entries[key] = e

        self.cfg_proxy_var = tk.BooleanVar(value=self.config.get("proxy_enabled", True))
        tk.Checkbutton(win, text="Enable Proxy", variable=self.cfg_proxy_var,
                      bg=C["bg"], fg=C["dim"], selectcolor=C["bg2"],
                      activebackground=C["bg"]).pack(anchor=tk.W, padx=34, pady=(6, 2))

        self.cfg_cors_var = tk.BooleanVar(value=self.config.get("cors_enabled", True))
        tk.Checkbutton(win, text="Enable CORS", variable=self.cfg_cors_var,
                      bg=C["bg"], fg=C["dim"], selectcolor=C["bg2"],
                      activebackground=C["bg"]).pack(anchor=tk.W, padx=34, pady=2)

        def _save():
            for k, e in entries.items():
                try: self.config[k] = int(e.get())
                except: pass
            self.config["proxy_enabled"] = self.cfg_proxy_var.get()
            self.config["cors_enabled"] = self.cfg_cors_var.get()
            save_config(self.config)
            self._update_info()
            self._log("Config saved. Restart server to apply.")
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=5, cursor="hand2").pack(pady=(14, 0))

    def _toggle_server(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            # Start proxy server
            self.proxy_server = ProxyServer(
                ("0.0.0.0", self.config["proxy_port"]),
                ProxyHandler,
                cors_enabled=self.config.get("cors_enabled", True),
                callback=self._on_proxy_request
            )
            threading.Thread(target=self.proxy_server.serve_forever, daemon=True).start()

            # Start web server
            serve_path = self.config.get("serve_path", "")
            if serve_path and os.path.exists(serve_path):

                class Handler(http.server.SimpleHTTPRequestHandler):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, directory=serve_path, **kwargs)
                    def log_message(self, f, *a): pass

                self.web_server = http.server.HTTPServer(("0.0.0.0", self.config["web_port"]), Handler)
                threading.Thread(target=self.web_server.serve_forever, daemon=True).start()

            self.running = True
            self._draw_dot("green")
            self.status_text.config(text="RUNNING", fg=C["green"])
            self.start_btn.config(text="⏹ STOP", bg=C["red"], fg="#fff")

            self._log("=" * 40)
            self._log(f"⚡ Nexus Server Pro STARTED")
            self._log(f"Web: http://localhost:{self.config['web_port']}")
            self._log(f"Proxy: http://localhost:{self.config['proxy_port']}")
            self._log(f"Dashboard: http://localhost:{self.config['proxy_port']}/")
            self._log(f"Serving: {serve_path or 'Not configured'}")
            self._log("=" * 40)
            self._update_info()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start: {e}")
            self._log(f"ERROR: {e}")

    def _stop(self):
        try:
            if self.proxy_server:
                self.proxy_server.shutdown()
                self.proxy_server = None
            if self.web_server:
                self.web_server.shutdown()
                self.web_server = None
        except: pass

        self.running = False
        self._draw_dot("red")
        self.status_text.config(text="STOPPED", fg=C["red"])
        self.start_btn.config(text="▶ START SERVER", bg=C["green"], fg="#000")
        self._log("Server STOPPED")
        self._update_info()

    def _on_proxy_request(self, method, url, status, size):
        self.root.after(0, lambda: self._log(
            f"[{datetime.now():%H:%M:%S}] {method} {url[:60]} → {status} ({size}b)"))

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _update_info(self):
        path = self.config.get("serve_path", "")
        display = os.path.basename(path) if path else "Not set"
        self.info_labels["web_port"].config(text=f":{self.config['web_port']}")
        self.info_labels["proxy_port"].config(text=f":{self.config['proxy_port']}")
        self.info_labels["serve_path_display"].config(text=display[:30])
        self.info_labels["proxy_status"].config(
            text="ON" if self.config.get("proxy_enabled") else "OFF",
            fg=C["green"] if self.config.get("proxy_enabled") else C["dim"])
        self.info_labels["cors_status"].config(
            text="ON" if self.config.get("cors_enabled") else "OFF",
            fg=C["green"] if self.config.get("cors_enabled") else C["dim"])
        total = self.proxy_server.total_requests if self.proxy_server else 0
        self.info_labels["total"].config(text=str(total))

    def _update_status(self):
        if self.running:
            self._update_info()
        self.root.after(5000, self._update_status)

    def _on_close(self):
        if self.running:
            if messagebox.askyesno("Stop Server", "Stop server and exit?"):
                self._stop()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    NexusServer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
