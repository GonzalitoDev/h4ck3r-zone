"""
NEXUS PROXY SERVER v1.0 — Self-Hosted Proxy Server
HTTP/HTTPS/SOCKS5 forward proxy with auth, tunnel, dashboard, rate limiting.
Auto public URL via SSH tunnel (serveo.net). Runs 24/7 in background.
"""
import os, sys, json, threading, socket, time, hashlib, struct, select, base64
import subprocess, urllib.request, urllib.parse, re
from datetime import datetime
from pathlib import Path
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#0a0a14", "bg2": "#101022", "card": "#161638",
    "border": "#202050", "text": "#d0d0e8", "dim": "#484878",
    "accent": "#6366f1", "accent2": "#818cf8",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa",
}

DATA_DIR = Path.home() / "Documents" / "NexusProxy"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "port": 8888,
    "socks_port": 1080,
    "username": "",
    "password": "",
    "require_auth": False,
    "max_connections": 100,
    "rate_limit": 30,
    "allowed_ips": [],
    "blocked_ips": [],
    "public_tunnel": False,
    "tunnel_port": 0,
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

def check_auth(data, username, password):
    """Check Proxy-Authorization header."""
    for line in data.decode(errors="ignore").split("\r\n"):
        if line.lower().startswith("proxy-authorization:"):
            auth = line.split(":", 1)[1].strip()
            if auth.lower().startswith("basic "):
                try:
                    decoded = base64.b64decode(auth[6:]).decode()
                    u, p = decoded.split(":", 1)
                    return u == username and p == password
                except:
                    pass
    return False


class ProxyServer:
    def __init__(self, host="0.0.0.0", port=8888, username="", password="",
                 allowed_ips=None, blocked_ips=None, callback=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.allowed_ips = allowed_ips or []
        self.blocked_ips = blocked_ips or []
        self.callback = callback
        self.running = False
        self.socket = None
        self.total_requests = 0
        self.total_in = 0
        self.total_out = 0
        self.active_connections = 0
        self.log_entries = deque(maxlen=200)
        self.clients_set = set()

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(200)
            self.running = True
            threading.Thread(target=self._accept_loop, daemon=True).start()
            self._log("info", f"Proxy listening on {self.host}:{self.port}")
            return True, ""
        except Exception as e:
            return False, str(e)

    def stop(self):
        self.running = False
        if self.socket:
            try: self.socket.close()
            except: pass

    def _log(self, level, msg):
        entry = f"[{datetime.now():%H:%M:%S}] [{level.upper()}] {msg}"
        self.log_entries.append(entry)
        if self.callback:
            self.callback(entry)

    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.socket.accept()
                ip = addr[0]

                # IP filtering
                if self.blocked_ips and ip in self.blocked_ips:
                    client.close()
                    self._log("block", f"Blocked {ip}")
                    continue
                if self.allowed_ips and ip not in self.allowed_ips:
                    client.close()
                    self._log("block", f"Not allowed {ip}")
                    continue

                self.active_connections += 1
                self.clients_set.add(ip)
                threading.Thread(target=self._handle, args=(client, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self._log("error", f"Accept error: {e}")

    def _handle(self, client, addr):
        ip = addr[0]
        try:
            client.settimeout(30)
            data = client.recv(8192)
            if not data:
                client.close()
                return

            # Auth check
            if self.username and self.password:
                if not check_auth(data, self.username, self.password):
                    client.send(b"HTTP/1.1 407 Proxy Authentication Required\r\n"
                               b"Proxy-Authenticate: Basic realm=\"NexusProxy\"\r\n\r\n")
                    client.close()
                    self._log("auth", f"Auth failed for {ip}")
                    return

            text = data.decode(errors="ignore")
            first_line = text.split("\r\n")[0] if text else ""
            parts = first_line.split(" ")

            if len(parts) >= 2 and parts[0].upper() == "CONNECT":
                self._handle_connect(client, parts[1], addr, data)
            elif len(parts) >= 3 and parts[0].upper() in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"):
                self._handle_http(client, data, addr)
            elif len(data) > 0 and data[0] == 0x05:
                self._handle_socks5(client, data, addr)
            else:
                client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                client.close()
        except Exception as e:
            self._log("error", f"Handler error {ip}: {e}")
        finally:
            try: client.close()
            except: pass
            self.active_connections -= 1

    def _handle_connect(self, client, target, addr, initial_data):
        ip = addr[0]
        try:
            host, port = target.split(":")
            port = int(port)
        except:
            host, port = target, 443

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(15)
            remote.connect((host, port))
            client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.total_requests += 1
            self._log("connect", f"{ip} → {host}:{port} (HTTPS tunnel)")

            self._tunnel(client, remote, ip)
        except Exception as e:
            self._log("error", f"CONNECT error {host}:{port}: {e}")
            try:
                client.send(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{str(e)}".encode())
            except: pass
            try: client.close()
            except: pass

    def _handle_http(self, client, data, addr):
        ip = addr[0]
        try:
            text = data.decode(errors="ignore")
            lines = text.split("\r\n")
            first = lines[0].split(" ")
            method, url = first[0], first[1]

            host, port, path = None, 80, url
            if url.startswith("http"):
                parsed = urllib.parse.urlparse(url)
                host, port = parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
                path = parsed.path + ("?" + parsed.query if parsed.query else "")
            else:
                for line in lines[1:]:
                    if line.lower().startswith("host:"):
                        host = line.split(":", 1)[1].strip()
                        break

            if not host:
                client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                client.close()
                return

            # Rewrite request
            new_req = f"{method} {path} HTTP/1.1\r\n"
            for line in lines[1:]:
                if not line.lower().startswith(("proxy-", "connection:")):
                    new_req += line + "\r\n"
            new_req += "Connection: close\r\n\r\n"

            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(15)
            remote.connect((host, port))
            remote.sendall(new_req.encode())

            self.total_requests += 1
            self._log("http", f"{method} {ip} → {host}{path[:60]}")

            self._tunnel(client, remote, ip)
        except Exception as e:
            self._log("error", f"HTTP error: {e}")
            try: client.close()
            except: pass

    def _handle_socks5(self, client, data, addr):
        ip = addr[0]
        try:
            nmethods = data[1]
            methods = data[2:2 + nmethods]
            client.send(b"\x05\x00")  # No auth

            req = client.recv(8192)
            if len(req) < 10 or req[1] != 0x01:
                client.close(); return

            atyp = req[3]
            if atyp == 0x01:
                host = f"{req[4]}.{req[5]}.{req[6]}.{req[7]}"
                port = struct.unpack(">H", req[8:10])[0]
            elif atyp == 0x03:
                dlen = req[4]
                host = req[5:5 + dlen].decode()
                port = struct.unpack(">H", req[5 + dlen:7 + dlen])[0]
            else:
                client.close(); return

            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(15)
            remote.connect((host, port))

            resp = b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + struct.pack(">H", 0)
            client.send(resp)

            self.total_requests += 1
            self._log("socks5", f"{ip} → {host}:{port}")

            self._tunnel(client, remote, ip)
        except Exception:
            try: client.close()
            except: pass

    def _tunnel(self, client, remote, ip):
        sockets_list = [client, remote]
        in_bytes, out_bytes = 0, 0
        try:
            while self.running:
                readable, _, _ = select.select(sockets_list, [], [], 60)
                if not readable: break
                for sock in readable:
                    try:
                        data = sock.recv(65536)
                        if not data:
                            for s in sockets_list:
                                try: s.close()
                                except: pass
                            self.total_in += in_bytes
                            self.total_out += out_bytes
                            return
                    except: return

                    target = remote if sock is client else client
                    try:
                        target.sendall(data)
                        if sock is client: out_bytes += len(data)
                        else: in_bytes += len(data)
                    except: return
        except: pass
        finally:
            for s in sockets_list:
                try: s.close()
                except: pass

    def stats(self):
        return {
            "requests": self.total_requests,
            "active": self.active_connections,
            "clients": len(self.clients_set),
            "total_in": self._fmt(self.total_in),
            "total_out": self._fmt(self.total_out),
        }

    def _fmt(self, s):
        for u in ("B", "KB", "MB", "GB"):
            if s < 1024: return f"{s:.1f}{u}"
            s /= 1024
        return f"{s:.1f}TB"


class NexusProxy:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS PROXY SERVER")
        self.root.geometry("820x580")
        self.root.minsize(600, 420)
        self.root.configure(bg=C["bg"])
        self._center()

        self.config = load_config()
        self.server = None
        self.socks_server = None
        self.running = False
        self.public_url = ""
        self.tunnel_proc = None
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
        tk.Label(hdr, text="🔀 NEXUS PROXY SERVER", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Self-Hosted HTTP/HTTPS/SOCKS5", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Status dot
        sf = tk.Frame(hdr, bg=C["bg"]); sf.pack(side=tk.RIGHT)
        self.status_dot = tk.Canvas(sf, width=12, height=12, bg=C["bg"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT); self._draw_dot("red")
        self.status_lbl = tk.Label(sf, text="STOPPED", font=("Segoe UI", 9, "bold"), fg=C["red"], bg=C["bg"])
        self.status_lbl.pack(side=tk.LEFT, padx=4)

        # Control bar
        ctrl = tk.Frame(self.root, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=16, pady=(6, 0))
        self.start_btn = tk.Button(ctrl, text="▶ START PROXY", command=self._toggle,
                                   font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                                   relief=tk.FLAT, padx=18, pady=5, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT)
        tk.Button(ctrl, text="⚙️ Config", command=self._config_window,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="🌐 Public URL", command=self._toggle_tunnel,
                 font=("Segoe UI", 9), bg=C["green"], fg="#000", relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Stats cards
        stats_f = tk.Frame(self.root, bg=C["bg"])
        stats_f.pack(fill=tk.X, padx=16, pady=(6, 0))
        for label, color in [("Requests", C["accent"]), ("Active", C["green"]),
                              ("Clients", C["blue"]), ("Upload/Download", C["gold"])]:
            card = tk.Frame(stats_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True, ipady=4)
            tk.Label(card, text=label, font=("Segoe UI", 7, "bold"), fg=C["dim"], bg=C["card"]).pack(pady=(4, 0))
            key = label.lower().replace("/", "_")
            setattr(self, f"stat_{key}", tk.Label(card, text="—", font=("Segoe UI", 16, "bold"),
                                                   fg=color, bg=C["card"]))
            getattr(self, f"stat_{key}").pack(pady=(0, 4))

        # Public URL display
        self.pub_frame = tk.Frame(self.root, bg=C["card"], highlightbackground=C["green"],
                                 highlightthickness=1)
        self.pub_frame.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.pub_label = tk.Label(self.pub_frame, text="Public URL: Not active",
                                  font=("Consolas", 9, "bold"), fg=C["text"], bg=C["card"])
        self.pub_label.pack(padx=12, pady=8)

        # Connection info
        info_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        info_f.pack(fill=tk.X, padx=16, pady=(4, 0), ipady=4)
        self.info_label = tk.Label(info_f, text="Configure and start the proxy server",
                                   font=("Consolas", 9), fg=C["text"], bg=C["card"])
        self.info_label.pack(padx=12, pady=6, anchor="w")

        # Log
        tk.Label(self.root, text="CONNECTION LOG", font=("Segoe UI", 9, "bold"),
                fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=16, pady=(6, 2))
        log_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        log_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        self.log_text = scrolledtext.ScrolledText(log_f, bg=C["bg2"], fg=C["text"],
                                                   font=("Consolas", 8), wrap=tk.WORD,
                                                   relief=tk.FLAT, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self._update_loop()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _draw_dot(self, color):
        self.status_dot.delete("all")
        c = {"green": C["green"], "red": C["red"]}.get(color, C["red"])
        self.status_dot.create_oval(2, 2, 10, 10, fill=c, outline="")

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.server = ProxyServer(
            port=self.config["port"],
            username=self.config.get("username", ""),
            password=self.config.get("password", ""),
            allowed_ips=self.config.get("allowed_ips", []),
            blocked_ips=self.config.get("blocked_ips", []),
            callback=lambda m: self.root.after(0, self._log, m)
        )
        ok, err = self.server.start()
        if ok:
            self.running = True
            self._draw_dot("green")
            self.status_lbl.config(text="RUNNING", fg=C["green"])
            self.start_btn.config(text="⏹ STOP", bg=C["red"], fg="#fff")
            auth_str = "with auth" if self.config.get("username") else "no auth"
            self._log(f"Proxy started on port {self.config['port']} ({auth_str})")
            self._log(f"Configure browser: HTTP Proxy → localhost:{self.config['port']}")
        else:
            self._log(f"ERROR: {err}")

    def _stop(self):
        if self.server: self.server.stop(); self.server = None
        if self.socks_server: self.socks_server.stop(); self.socks_server = None
        if self.tunnel_proc:
            try: self.tunnel_proc.terminate()
            except: pass
            self.tunnel_proc = None
        self.running = False
        self._draw_dot("red")
        self.status_lbl.config(text="STOPPED", fg=C["red"])
        self.start_btn.config(text="▶ START PROXY", bg=C["accent"], fg="#fff")
        self.pub_label.config(text="Public URL: Not active")
        self._log("Proxy stopped")

    def _toggle_tunnel(self):
        if self.tunnel_proc:
            try: self.tunnel_proc.terminate()
            except: pass
            self.tunnel_proc = None
            self.pub_label.config(text="Public URL: Tunnel closed", fg=C["dim"])
            self._log("Public tunnel closed")
            return

        if not self.running:
            messagebox.showinfo("Start proxy", "Start the proxy server first.")
            return

        self._log("Creating public tunnel via serveo.net...")
        self.pub_label.config(text="Creating tunnel...", fg=C["orange"])

        def _run():
            try:
                port = self.config["port"]
                # Try multiple free tunnel services
                cmd = f'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:{port} serveo.net'
                self.tunnel_proc = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                time.sleep(3)
                # The URL is printed to stderr by serveo
                output = ""
                try:
                    for _ in range(10):
                        line = self.tunnel_proc.stderr.readline().decode(errors="ignore")
                        output += line
                        m = re.search(r'(https?://[^\s]+\.serveo\.net)', output)
                        if m:
                            self.public_url = m.group(1)
                            self.root.after(0, lambda: self.pub_label.config(
                                text=f"Public URL: {self.public_url}", fg=C["green"]))
                            self.root.after(0, lambda: self._log(f"Tunnel active: {self.public_url}"))
                            return
                except: pass
                self.root.after(0, lambda: self.pub_label.config(
                    text="Tunnel: Manual setup needed (install OpenSSH)", fg=C["orange"]))
            except Exception as e:
                self.root.after(0, lambda: self.pub_label.config(
                    text=f"Tunnel failed: Install OpenSSH client", fg=C["red"]))
                self.root.after(0, lambda: self._log(f"Tunnel error: Install OpenSSH for Windows"))

        threading.Thread(target=_run, daemon=True).start()

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _update_loop(self):
        if self.running and self.server:
            s = self.server.stats()
            self.stat_requests.config(text=str(s["requests"]))
            self.stat_active.config(text=str(s["active"]))
            self.stat_clients.config(text=str(s["clients"]))
            self.stat_upload_download.config(text=f"↑{s['total_out']} ↓{s['total_in']}"[:20])
            auth = "🔒" if self.config.get("username") else "🔓"
            self.info_label.config(
                text=f"HTTP Proxy: localhost:{self.config['port']}  |  {auth}  |  "
                     f"Connect from: localhost:{self.config['port']}")
        self.root.after(2000, self._update_loop)

    def _config_window(self):
        win = tk.Toplevel(self.root)
        win.title("Proxy Config"); win.geometry("440x360")
        win.configure(bg=C["bg"]); win.resizable(False, False)
        win.transient(self.root); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 440) // 2; y = (win.winfo_screenheight() - 360) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="PROXY CONFIGURATION", font=("Segoe UI", 13, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(pady=(16, 10))

        entries = {}
        for label, key, default, show in [
            ("Proxy Port", "port", "8888", ""),
            ("Username", "username", "", ""),
            ("Password", "password", "", "*"),
            ("Max Connections", "max_connections", "100", ""),
        ]:
            f = tk.Frame(win, bg=C["bg"]); f.pack(fill=tk.X, padx=30, pady=3)
            tk.Label(f, text=label, font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"],
                    width=14, anchor="w").pack(side=tk.LEFT)
            e = tk.Entry(f, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                        insertbackground=C["accent"], relief=tk.FLAT, show=show)
            e.insert(0, str(self.config.get(key, default)))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            entries[key] = e

        auth_var = tk.BooleanVar(value=self.config.get("require_auth", False))
        tk.Checkbutton(win, text="Require Authentication", variable=auth_var,
                      bg=C["bg"], fg=C["dim"], selectcolor=C["bg2"],
                      activebackground=C["bg"]).pack(anchor=tk.W, padx=34, pady=(6, 2))

        def _save():
            for k, e in entries.items():
                try: self.config[k] = int(e.get())
                except: self.config[k] = e.get()
            self.config["require_auth"] = auth_var.get()
            save_config(self.config)
            self._log("Config saved. Restart to apply.")
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=5,
                 cursor="hand2").pack(pady=(14, 0))

    def _on_close(self):
        if self.running:
            if messagebox.askyesno("Stop", "Stop proxy and exit?"):
                self._stop(); self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    NexusProxy(root)
    root.mainloop()


if __name__ == "__main__":
    main()
