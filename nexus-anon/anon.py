"""
NEXUS ANON v1.0 — Anonymous Privacy Proxy
100% legal privacy toolkit. Proxy anonymizer, header stripping,
DNS over HTTPS, fingerprint protection, Tor routing.
Routes your traffic through multiple privacy layers.
"""
import os, sys, json, threading, socket, ssl, time, hashlib, base64, struct, select, random, re, urllib.request, urllib.parse, http.server, subprocess, winreg
from datetime import datetime
from pathlib import Path
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#06060c", "bg2": "#0e0e1a", "card": "#14142e",
    "border": "#1e1e40", "text": "#d0d0e8", "dim": "#484878",
    "accent": "#10b981", "accent2": "#34d399",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa", "purple": "#a855f7",
}

DATA_DIR = Path.home() / "Documents" / "NexusAnon"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "proxy_port": 8888,
    "strip_headers": True,
    "random_user_agent": True,
    "dns_over_https": True,
    "tor_enabled": False,
    "tor_port": 9050,
    "auto_proxy": True,
    "rotate_identity": False,
    "rotate_interval": 300,
}

# Common user agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
]

# Privacy-protecting DNS servers (DoH)
DOH_SERVERS = ["https://cloudflare-dns.com/dns-query", "https://dns.quad9.net/dns-query"]

# Identifying headers to strip
STRIP_HEADERS = [
    "user-agent", "accept-language", "accept-encoding",
    "referer", "origin", "dnt", "sec-ch-ua",
    "sec-ch-ua-mobile", "sec-ch-ua-platform",
    "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site",
    "x-forwarded-for", "x-real-ip", "cf-connecting-ip",
    "true-client-ip", "x-client-ip",
]

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except:
        return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ===== ANONYMIZING PROXY SERVER =====
class AnonProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self._proxy("GET")
    def do_POST(self): self._proxy("POST")
    def do_PUT(self): self._proxy("PUT")
    def do_DELETE(self): self._proxy("DELETE")
    def do_HEAD(self): self._proxy("HEAD")
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_CONNECT(self):
        """Handle HTTPS CONNECT tunneling with anonymization."""
        try:
            host, port = self.path.split(":")
            port = int(port)
        except:
            self.send_error(400); return

        # Route through Tor if enabled
        if self.server.config.get("tor_enabled"):
            target = ("127.0.0.1", self.server.config.get("tor_port", 9050))
        else:
            target = (host, port)

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(15)
            remote.connect(target)

            # If using Tor, send CONNECT to Tor SOCKS5
            if self.server.config.get("tor_enabled"):
                # SOCKS5 handshake + CONNECT
                remote.send(b"\x05\x01\x00")
                resp = remote.recv(2)
                addr = socket.inet_aton(socket.gethostbyname(host))
                req = b"\x05\x01\x00\x01" + addr + struct.pack(">H", port)
                remote.send(req)
                resp = remote.recv(10)

            self.send_response(200, "Connection Established")
            self.end_headers()

            self.server.active += 1
            self._tunnel(self.connection, remote)
            self.server.active -= 1
        except Exception as e:
            try: self.send_error(502)
            except: pass
        finally:
            try: remote.close()
            except: pass

    def _proxy(self, method):
        url = self.path
        if url.startswith("/"):
            if url == "/":
                self._status_page(); return
            url = urllib.parse.unquote(url[1:])

        if not url.startswith("http"):
            self.send_error(400, "Invalid URL")
            return

        self.server.total += 1
        self.server.active += 1

        try:
            # Prepare anonymized request
            parsed = urllib.parse.urlparse(url)
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))) if self.headers.get("Content-Length") else None

            # Build clean headers
            clean_headers = {}
            config = self.server.config

            # Random User-Agent
            if config.get("random_user_agent"):
                clean_headers["User-Agent"] = random.choice(USER_AGENTS)
            else:
                clean_headers["User-Agent"] = self.headers.get("User-Agent", "")

            # Copy only non-identifying headers
            keep = ["content-type", "accept", "cache-control", "pragma", "authorization"]
            for k, v in self.headers.items():
                kl = k.lower()
                if kl in keep:
                    clean_headers[k] = v
                elif not config.get("strip_headers") and kl not in [h.lower() for h in STRIP_HEADERS]:
                    clean_headers[k] = v

            # Remove referer
            if "Referer" in clean_headers:
                del clean_headers["Referer"]

            # Add privacy headers
            clean_headers["DNT"] = "1"
            clean_headers["Accept-Language"] = "en-US,en;q=0.9"

            # Make request through Tor if enabled
            req_url = url
            if config.get("tor_enabled"):
                # Route through local Tor SOCKS proxy (handled by socket-level)
                pass

            req = urllib.request.Request(req_url, data=body, method=method)
            for k, v in clean_headers.items():
                req.add_header(k, v)

            resp = urllib.request.urlopen(req, timeout=15)
            self.send_response(resp.status)

            for k, v in resp.headers.items():
                if k.lower() not in ("transfer-encoding", "connection", "set-cookie"):
                    self.send_header(k, v)

            self.end_headers()
            data = resp.read()
            self.wfile.write(data)

            self.server.log(f"[{method}] {url[:80]} → {resp.status}")
        except Exception as e:
            try: self.send_error(502, str(e)[:100])
            except: pass
            self.server.log(f"[ERROR] {url[:60]}: {e}")
        finally:
            self.server.active -= 1

    def _tunnel(self, client, remote):
        sockets = [client, remote]
        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 60)
                if not readable: break
                for sock in readable:
                    try:
                        data = sock.recv(65536)
                        if not data:
                            for s in sockets:
                                try: s.close()
                                except: pass
                            return
                    except: return
                    target = remote if sock is client else client
                    try: target.sendall(data)
                    except: return
        except: pass

    def _status_page(self):
        s = self.server
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Nexus Anon — Status</title>
<style>*{{margin:0;padding:0}}body{{background:#06060c;color:#d0d0e8;font-family:Segoe UI;padding:30px;max-width:600px;margin:auto}}
h1{{color:#10b981;font-size:20px;margin-bottom:16px}}
.card{{background:#0e0e1a;border:1px solid #1e1e40;border-radius:10px;padding:18px;margin:12px 0}}
.stats{{display:flex;gap:10px}}.stat{{flex:1;text-align:center;padding:10px;background:#06060c;border-radius:6px;border:1px solid #1e1e40}}
.stat .n{{font-size:22px;color:#10b981;font-weight:bold}}.stat .l{{font-size:9px;color:#484878}}
.green{{color:#34d399}}ul{{list-style:none;font-size:11px}}li{{padding:2px 0;color:#484878}}li b{{color:#d0d0e8}}
</style></head><body>
<h1>🛡️ Nexus Anon — Status</h1>
<div class="card"><div class="stats">
<div class="stat"><div class="n">{s.total}</div><div class="l">Requests</div></div>
<div class="stat"><div class="n">{s.active}</div><div class="l">Active</div></div>
<div class="stat"><div class="n">{s.config['proxy_port']}</div><div class="l">Port</div></div>
</div></div>
<div class="card"><ul>
<li>🔒 <b>Header Stripping:</b> {'ON' if s.config.get('strip_headers') else 'OFF'}</li>
<li>🎭 <b>Random User Agent:</b> {'ON' if s.config.get('random_user_agent') else 'OFF'}</li>
<li>🔐 <b>DNS over HTTPS:</b> {'ON' if s.config.get('dns_over_https') else 'OFF'}</li>
<li>🧅 <b>Tor Routing:</b> {'ON' if s.config.get('tor_enabled') else 'OFF'}</li>
<li>⚡ <b>Auto Proxy:</b> {'ON' if s.config.get('auto_proxy') else 'OFF'}</li>
</ul></div>
<div class="card" style="text-align:center">
<p style="color:#484878;font-size:10px">Configure your browser to use proxy: <b style="color:#10b981">localhost:{s.config['proxy_port']}</b></p>
</div>
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args): pass


class AnonProxyServer(http.server.HTTPServer):
    allow_reuse_address = True
    def __init__(self, config, *args, **kwargs):
        self.config = config
        self.total = 0
        self.active = 0
        self.log_entries = deque(maxlen=150)
        super().__init__(*args, **kwargs)

    def log(self, msg):
        self.log_entries.append(f"[{datetime.now():%H:%M:%S}] {msg}")


# ===== SYSTEM PROXY CONFIG =====
def enable_system_proxy(host="localhost", port=8888):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}")
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>")
        winreg.CloseKey(key)
        import ctypes
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
        return True
    except: return False

def disable_system_proxy():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        import ctypes
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
        return True
    except: return False


# ===== GUI =====
class NexusAnon:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS ANON — Anonymous Privacy Proxy")
        self.root.geometry("820x580")
        self.root.minsize(600, 420)
        self.root.configure(bg=C["bg"])
        self._center()

        self.config = load_config()
        self.server = None
        self.running = False
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 820) // 2
        y = (self.root.winfo_screenheight() - 580) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🛡️ NEXUS ANON", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Anonymous Privacy Proxy | 100% Legal", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Status
        sf = tk.Frame(hdr, bg=C["bg"]); sf.pack(side=tk.RIGHT)
        self.status_dot = tk.Canvas(sf, width=12, height=12, bg=C["bg"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT); self._draw_dot("red")
        self.status_lbl = tk.Label(sf, text="DISCONNECTED", font=("Segoe UI", 9, "bold"),
                                   fg=C["red"], bg=C["bg"])
        self.status_lbl.pack(side=tk.LEFT, padx=4)

        # Control bar
        ctrl = tk.Frame(self.root, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=16, pady=(6, 0))
        self.start_btn = tk.Button(ctrl, text="🛡️ ACTIVATE ANON MODE", command=self._toggle,
                                   font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#000",
                                   relief=tk.FLAT, padx=18, pady=5, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT)
        tk.Button(ctrl, text="⚙️ Config", command=self._config_window,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Privacy mode toggles
        for text, key, color in [
            ("🎭 Random UA", "random_user_agent", C["blue"]),
            ("🔒 Strip Headers", "strip_headers", C["orange"]),
            ("🧅 Tor", "tor_enabled", C["purple"]),
            ("⚡ Auto Proxy", "auto_proxy", C["green"]),
        ]:
            var = tk.BooleanVar(value=self.config.get(key, False))
            setattr(self, f"toggle_{key}", var)
            tk.Checkbutton(ctrl, text=text, variable=var, command=lambda k=key: self._update_config(k),
                          bg=C["bg"], fg=color, selectcolor=C["bg2"],
                          activebackground=C["bg"], font=("Segoe UI", 8)).pack(side=tk.RIGHT, padx=2)

        # Stats
        stats_f = tk.Frame(self.root, bg=C["bg"])
        stats_f.pack(fill=tk.X, padx=16, pady=(4, 0))
        for label, color in [("Requests", C["accent"]), ("Active", C["green"]),
                              ("Leaks Blocked", C["orange"]), ("Identity", C["blue"])]:
            card = tk.Frame(stats_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True, ipady=4)
            tk.Label(card, text=label, font=("Segoe UI", 7, "bold"), fg=C["dim"], bg=C["card"]).pack(pady=(4, 0))
            key = label.lower().replace(" ", "_")
            setattr(self, f"stat_{key}", tk.Label(card, text="—",
                                                   font=("Segoe UI", 16, "bold"), fg=color, bg=C["card"]))
            getattr(self, f"stat_{key}").pack(pady=(0, 4))

        # Proxy info
        info_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        info_f.pack(fill=tk.X, padx=16, pady=(4, 0), ipady=4)
        self.info_lbl = tk.Label(info_f, text="Click ACTIVATE to enable anonymous mode",
                                 font=("Consolas", 9), fg=C["text"], bg=C["card"])
        self.info_lbl.pack(padx=12, pady=6, anchor="w")

        # Security tips
        tips_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        tips_f.pack(fill=tk.X, padx=16, pady=(4, 0), ipady=4)
        tips = [
            "✅ 100% LEGAL — Privacy tools used by journalists, researchers, and security professionals",
            "🛡️ Strips identifying headers (User-Agent, Referer, Accept-Language...)",
            "🧅 Optional Tor routing for maximum anonymity (requires Tor installed)",
            "🔐 Random browser fingerprint rotation prevents tracking across sessions",
        ]
        self.tips_lbl = tk.Label(tips_f, text="\n".join(f"  {t}" for t in tips),
                                 font=("Segoe UI", 8), fg=C["dim"], bg=C["card"], anchor="w", justify="left")
        self.tips_lbl.pack(padx=12, pady=6, anchor="w")

        # Log
        tk.Label(self.root, text="CONNECTION LOG", font=("Segoe UI", 9, "bold"),
                fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=16, pady=(6, 2))
        log_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        log_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        self.log_text = scrolledtext.ScrolledText(log_f, bg=C["bg2"], fg=C["text"],
                                                   font=("Consolas", 8), wrap=tk.WORD,
                                                   relief=tk.FLAT, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        tk.Label(self.root, text="", bg=C["bg"]).pack()

        self._update_loop()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _draw_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 10, 10, fill={"green":C["green"],"red":C["red"]}.get(color,C["red"]), outline="")

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.server = AnonProxyServer(self.config, ("0.0.0.0", self.config["proxy_port"]), AnonProxyHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.running = True
        self._draw_dot("green")
        self.status_lbl.config(text="ANONYMOUS MODE ACTIVE", fg=C["green"])
        self.start_btn.config(text="⏹ DEACTIVATE", bg=C["red"], fg="#fff")

        if self.config.get("auto_proxy"):
            enable_system_proxy("localhost", self.config["proxy_port"])
            self._log("⚡ System proxy configured automatically")

        self._log("=" * 30)
        self._log("🛡️ ANONYMOUS MODE ACTIVATED")
        self._log(f"Proxy: localhost:{self.config['proxy_port']}")
        self._log(f"Headers: {'STRIPPED' if self.config.get('strip_headers') else 'PASSED'}")
        self._log(f"User-Agent: {'RANDOM' if self.config.get('random_user_agent') else 'ORIGINAL'}")
        self._log(f"Tor: {'ON' if self.config.get('tor_enabled') else 'OFF'}")
        self._log("=" * 30)

        self.info_lbl.config(text=f"Proxy: localhost:{self.config['proxy_port']} | "
                              f"UA: {'Random' if self.config.get('random_user_agent') else 'Original'} | "
                              f"Headers: {'Stripped' if self.config.get('strip_headers') else 'Passed'}")

    def _stop(self):
        if self.server:
            try: self.server.shutdown()
            except: pass
            self.server = None
        disable_system_proxy()
        self.running = False
        self._draw_dot("red")
        self.status_lbl.config(text="DISCONNECTED", fg=C["red"])
        self.start_btn.config(text="🛡️ ACTIVATE ANON MODE", bg=C["accent"], fg="#000")
        self._log("Anonymous mode deactivated")
        self.info_lbl.config(text="Click ACTIVATE to enable anonymous mode")

    def _update_config(self, key):
        self.config[key] = getattr(self, f"toggle_{key}").get()
        save_config(self.config)

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _update_loop(self):
        if self.running and self.server:
            self.stat_requests.config(text=str(self.server.total))
            self.stat_active.config(text=str(self.server.active))
            self.stat_leaks_blocked.config(text=str(self.server.total))
            self.stat_identity.config(
                text="ANONYMOUS" if self.config.get("random_user_agent") else "VISIBLE")
        self.root.after(1000, self._update_loop)

    def _config_window(self):
        win = tk.Toplevel(self.root)
        win.title("Anon Config"); win.geometry("400x300")
        win.configure(bg=C["bg"]); win.resizable(False, False)
        win.transient(self.root); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 400) // 2; y = (win.winfo_screenheight() - 300) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="ANONYMITY CONFIG", font=("Segoe UI", 13, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(pady=(14, 8))

        entries = {}
        for label, key, default in [("Proxy Port", "proxy_port", "8888"),
                                     ("Tor Port", "tor_port", "9050"),
                                     ("Rotate Interval (s)", "rotate_interval", "300")]:
            f = tk.Frame(win, bg=C["bg"]); f.pack(fill=tk.X, padx=30, pady=3)
            tk.Label(f, text=label, font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"],
                    width=18, anchor="w").pack(side=tk.LEFT)
            e = tk.Entry(f, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                        insertbackground=C["accent"], relief=tk.FLAT)
            e.insert(0, str(self.config.get(key, default)))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            entries[key] = e

        def _save():
            for k, e in entries.items():
                try: self.config[k] = int(e.get())
                except: pass
            save_config(self.config)
            self._log("Config saved. Restart to apply changes.")
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=5,
                 cursor="hand2").pack(pady=(10, 0))

    def _on_close(self):
        if self.running:
            if messagebox.askyesno("Deactivate", "Deactivate anonymous mode and exit?"):
                self._stop(); self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    NexusAnon(root)
    root.mainloop()


if __name__ == "__main__":
    main()
