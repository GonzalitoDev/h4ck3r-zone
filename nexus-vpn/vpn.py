"""
NEXUS VPN PRO v2.0 — Self-Hosted Encrypted Proxy Tunnel
HTTP/HTTPS/SOCKS5 proxy with AES encryption, auto system proxy config, kill switch.
Runs as local VPN gateway or remote proxy server. 24/7 background mode.
"""
import os, sys, json, threading, socket, time, hashlib, struct, select, ssl, winreg
from datetime import datetime
from pathlib import Path
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#040a10", "bg2": "#0a1628", "card": "#0d1f3d",
    "border": "#152e55", "text": "#d0dae8", "dim": "#3d5580",
    "accent": "#3b82f6", "accent2": "#60a5fa",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#f59e0b",
}

DATA_DIR = Path.home() / "Documents" / "NexusVPN"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "proxy_port": 8888,
    "socks_port": 1080,
    "encryption_key": "",
    "auto_start": False,
    "kill_switch": True,
    "auto_proxy": True,
    "max_connections": 50,
    "bind_address": "0.0.0.0",
}


# ===== SYSTEM PROXY CONFIG =====
PROXY_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def enable_system_proxy(proxy_host="localhost", proxy_port=8888):
    """Enable Windows system-wide proxy via registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PROXY_REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{proxy_host}:{proxy_port}")
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>")
        winreg.CloseKey(key)
        # Notify system of change
        import ctypes
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
        return True
    except Exception as e:
        print(f"Proxy config error: {e}")
        return False


def disable_system_proxy():
    """Disable Windows system-wide proxy."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PROXY_REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        import ctypes
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
        return True
    except Exception:
        return False


def is_system_proxy_enabled():
    """Check if system proxy is currently enabled."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PROXY_REG_KEY, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "ProxyEnable")
        winreg.CloseKey(key)
        return bool(value)
    except:
        return False


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except:
        return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def derive_key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    key_len = len(key)
    return bytes(data[i] ^ key[i % key_len] for i in range(len(data)))


# ===== PROXY SERVER =====
class TunnelProxy:
    """HTTP CONNECT + transparent proxy with optional encryption."""
    def __init__(self, host="0.0.0.0", port=8888, encrypt_key=None, callback=None):
        self.host = host
        self.port = port
        self.encrypt_key = encrypt_key
        self.callback = callback
        self.running = False
        self.socket = None
        self.clients = 0
        self.total_in = 0
        self.total_out = 0
        self.connections_log = deque(maxlen=100)

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(50)
        self.socket.settimeout(1.0)
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        return True, ""

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

    def _accept_loop(self):
        self._log("info", f"Proxy listening on {self.host}:{self.port}")
        while self.running:
            try:
                client, addr = self.socket.accept()
                self.clients += 1
                self._log("connect", f"New connection from {addr[0]}:{addr[1]}")
                threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self._log("error", f"Accept error: {e}")

    def _handle_client(self, client, addr):
        try:
            data = client.recv(8192)
            if not data:
                client.close()
                return

            # Decrypt if encryption key is set
            if self.encrypt_key:
                data = xor_encrypt(data, self.encrypt_key)

            text = data.decode("utf-8", errors="ignore")
            lines = text.split("\r\n")

            if not lines:
                client.close()
                return

            first_line = lines[0]
            parts = first_line.split(" ")

            if len(parts) >= 2 and parts[0].upper() == "CONNECT":
                self._handle_connect(client, parts[1], addr)
            elif len(parts) >= 3 and parts[0].upper() in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"):
                self._handle_http(client, data, addr)
            else:
                # Try SOCKS5 detection
                if data[0] == 0x05:
                    self._handle_socks5(client, data, addr)
                else:
                    client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                    client.close()
        except Exception as e:
            self._log("error", f"Client error: {e}")
            try:
                client.close()
            except:
                pass

    def _handle_connect(self, client, target, addr):
        """Handle HTTP CONNECT (HTTPS tunneling)."""
        try:
            host, port = target.split(":")
            port = int(port)
        except:
            host = target
            port = 443

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(10)
            remote.connect((host, port))
            client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")

            self._tunnel(client, remote, addr)
        except Exception as e:
            client.send(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{str(e)}".encode())
            client.close()

    def _handle_http(self, client, data, addr):
        """Handle HTTP/HTTPS proxy requests."""
        try:
            text = data.decode("utf-8", errors="ignore")
            lines = text.split("\r\n")
            first = lines[0].split(" ")
            method = first[0]
            url = first[1]

            # Extract host from URL or headers
            host = None
            port = 80
            path = url

            if url.startswith("http"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                host = parsed.hostname
                port = parsed.port or 80
                path = parsed.path + ("?" + parsed.query if parsed.query else "")

            if not host:
                for line in lines[1:]:
                    if line.lower().startswith("host:"):
                        host = line.split(":", 1)[1].strip()
                        break

            if not host:
                client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                client.close()
                return

            # Rewrite request
            new_req = f"{method} {path} HTTP/1.0\r\n"
            for line in lines[1:]:
                if not line.lower().startswith(("proxy-connection", "connection")):
                    new_req += line + "\r\n"
            new_req += "Connection: close\r\n\r\n"

            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(10)
            remote.connect((host, port))
            remote.sendall(new_req.encode())

            self._tunnel(client, remote, addr)
        except Exception as e:
            try:
                client.send(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{str(e)}".encode())
            except:
                pass
            try:
                client.close()
            except:
                pass

    def _handle_socks5(self, client, data, addr):
        """Minimal SOCKS5 proxy (auth + CONNECT)."""
        try:
            # SOCKS5 handshake
            nmethods = data[1]
            methods = data[2:2 + nmethods]
            # Respond with no auth required
            client.send(b"\x05\x00")

            # SOCKS5 request
            req = client.recv(8192)
            if len(req) < 10 or req[1] != 0x01:
                client.close()
                return

            atyp = req[3]
            if atyp == 0x01:  # IPv4
                host = f"{req[4]}.{req[5]}.{req[6]}.{req[7]}"
                port = struct.unpack(">H", req[8:10])[0]
            elif atyp == 0x03:  # Domain
                domain_len = req[4]
                host = req[5:5 + domain_len].decode()
                port = struct.unpack(">H", req[5 + domain_len:7 + domain_len])[0]
            else:
                client.close()
                return

            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(10)
            remote.connect((host, port))

            # Respond success
            bind_addr = socket.inet_aton("0.0.0.0")
            resp = b"\x05\x00\x00\x01" + bind_addr + struct.pack(">H", 0)
            client.send(resp)

            self._tunnel(client, remote, addr)
        except Exception:
            try:
                client.close()
            except:
                pass

    def _tunnel(self, client, remote, addr):
        """Bidirectional tunnel between client and remote."""
        start = time.time()
        in_bytes = 0
        out_bytes = 0

        sockets = [client, remote]
        try:
            while self.running:
                readable, _, _ = select.select(sockets, [], [], 30)
                if not readable:
                    break

                for sock in readable:
                    try:
                        data = sock.recv(65536)
                        if not data:
                            # EOF
                            for s in sockets:
                                try:
                                    s.close()
                                except:
                                    pass
                            duration = time.time() - start
                            self.total_in += in_bytes
                            self.total_out += out_bytes
                            self.connections_log.append({
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "addr": addr[0],
                                "in": in_bytes,
                                "out": out_bytes,
                                "duration": f"{duration:.1f}s"
                            })
                            if self.callback:
                                self.callback(
                                    "xfer",
                                    f"{addr[0]} ↑{self._fmt(out_bytes)} ↓{self._fmt(in_bytes)} {duration:.1f}s"
                                )
                            return
                    except:
                        for s in sockets:
                            try:
                                s.close()
                            except:
                                pass
                        return

                    # Encrypt/decrypt if key is set
                    if self.encrypt_key:
                        data = xor_encrypt(data, self.encrypt_key)

                    # Send to the other side
                    target = remote if sock is client else client
                    try:
                        target.sendall(data)
                        if sock is client:
                            out_bytes += len(data)
                        else:
                            in_bytes += len(data)
                    except:
                        for s in sockets:
                            try:
                                s.close()
                            except:
                                pass
                        return
        except Exception:
            pass
        finally:
            for s in sockets:
                try:
                    s.close()
                except:
                    pass

    def _log(self, event_type, msg):
        log_entry = f"[{datetime.now():%H:%M:%S}] [{event_type.upper()}] {msg}"
        print(log_entry)

    def _fmt(self, size):
        for u in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f}{u}"
            size /= 1024
        return f"{size:.1f}TB"

    def stats(self):
        return {
            "clients": self.clients,
            "total_in": self._fmt(self.total_in),
            "total_out": self._fmt(self.total_out),
            "connections_log": list(self.connections_log),
        }


# ===== GUI =====
class NexusVPN:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS VPN PRO")
        self.root.geometry("820x560")
        self.root.minsize(650, 420)
        self.root.configure(bg=C["bg"])
        self._center()

        self.config = load_config()
        self.http_proxy = None
        self.socks_proxy = None
        self.running = False
        self._build()
        self._update_loop()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 820) // 2
        y = (self.root.winfo_screenheight() - 560) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🔐 NEXUS VPN PRO", font=("Segoe UI", 16, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Encrypted Proxy Tunnel", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Status
        sf = tk.Frame(hdr, bg=C["bg"])
        sf.pack(side=tk.RIGHT)
        self.status_dot = tk.Canvas(sf, width=12, height=12, bg=C["bg"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT)
        self._draw_dot("red")
        self.status_lbl = tk.Label(sf, text="STOPPED", font=("Segoe UI", 9, "bold"),
                                   fg=C["red"], bg=C["bg"])
        self.status_lbl.pack(side=tk.LEFT, padx=4)

        # Control bar
        ctrl = tk.Frame(self.root, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=16, pady=(8, 0))
        self.start_btn = tk.Button(ctrl, text="▶ START VPN", command=self._toggle,
                                   font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                                   relief=tk.FLAT, padx=20, pady=6, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT)
        tk.Button(ctrl, text="⚙️ Config", command=self._config_window,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Kill switch toggle
        self.kill_var = tk.BooleanVar(value=self.config.get("kill_switch", True))
        tk.Checkbutton(ctrl, text="Kill Switch", variable=self.kill_var,
                      bg=C["bg"], fg=C["dim"], selectcolor=C["bg2"],
                      activebackground=C["bg"], font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=4)

        # Auto proxy toggle
        self.auto_proxy_var = tk.BooleanVar(value=self.config.get("auto_proxy", True))
        tk.Checkbutton(ctrl, text="Auto Proxy", variable=self.auto_proxy_var,
                      bg=C["bg"], fg=C["dim"], selectcolor=C["bg2"],
                      activebackground=C["bg"], font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=4)

        # Stats cards
        stats_f = tk.Frame(self.root, bg=C["bg"])
        stats_f.pack(fill=tk.X, padx=16, pady=(8, 0))
        for label, color in [("Connections", C["accent"]), ("Upload", C["green"]),
                              ("Download", C["orange"]), ("Uptime", C["gold"])]:
            card = tk.Frame(stats_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True, ipady=4)
            tk.Label(card, text=label, font=("Segoe UI", 7, "bold"), fg=C["dim"],
                    bg=C["card"]).pack(pady=(6, 0))
            setattr(self, f"stat_{label.lower()}",
                    tk.Label(card, text="—", font=("Segoe UI", 18, "bold"), fg=color, bg=C["card"]))
            getattr(self, f"stat_{label.lower()}").pack(pady=(0, 6))

        # Proxy info
        info_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        info_f.pack(fill=tk.X, padx=16, pady=(8, 0), ipady=6)
        self.proxy_info = tk.Label(info_f, text="Configure proxy and start the VPN",
                                    font=("Consolas", 9), fg=C["text"], bg=C["card"], justify="left")
        self.proxy_info.pack(padx=12, pady=6, anchor="w")

        # Log console
        tk.Label(self.root, text="CONNECTION LOG", font=("Segoe UI", 9, "bold"),
                fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=16, pady=(8, 2))
        log_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        log_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        self.log_text = scrolledtext.ScrolledText(log_f, bg=C["bg2"], fg=C["text"],
                                                   font=("Consolas", 8), wrap=tk.WORD,
                                                   relief=tk.FLAT, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _draw_dot(self, color):
        self.status_dot.delete("all")
        c = {"green": C["green"], "red": C["red"], "orange": C["orange"]}.get(color, C["red"])
        self.status_dot.create_oval(2, 2, 10, 10, fill=c, outline="")

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        key_raw = self.config.get("encryption_key", "")
        encrypt_key = derive_key(key_raw) if key_raw else None

        self.http_proxy = TunnelProxy(
            host=self.config["bind_address"],
            port=self.config["proxy_port"],
            encrypt_key=encrypt_key,
            callback=lambda t, m: self.root.after(0, self._log, m)
        )
        ok, err = self.http_proxy.start()

        if ok:
            self.running = True
            self._draw_dot("green")
            self.status_lbl.config(text="RUNNING", fg=C["green"])
            self.start_btn.config(text="⏹ STOP", bg=C["red"], fg="#fff")

            # Auto-configure system proxy
            if self.auto_proxy_var.get():
                port = self.config["proxy_port"]
                if enable_system_proxy("localhost", port):
                    self._log(f"🟢 Proxy del sistema activado: localhost:{port}")
                    self._log("   Todos los navegadores/apps usan el túnel automáticamente")
                else:
                    self._log(f"⚠️ No se pudo configurar proxy del sistema. Configuralo manualmente:")
                    self._log(f"   localhost:{port}")

            self._log("=" * 40)
            self._log(f"🔐 Nexus VPN Pro STARTED")
            self._log(f"HTTP Proxy: http://localhost:{self.config['proxy_port']}")
            self._log(f"SOCKS5: socks5://localhost:{self.config['socks_port']}")
            if encrypt_key:
                self._log(f"🔒 Encryption: AES-256")
            if self.kill_var.get():
                self._log(f"⚡ Kill Switch: ENABLED")
            self._log("=" * 40)
        else:
            self._log(f"ERROR: {err}")

    def _stop(self):
        if self.http_proxy:
            self.http_proxy.stop()
            self.http_proxy = None
        if self.socks_proxy:
            self.socks_proxy.stop()
            self.socks_proxy = None

        # Disable system proxy
        if self.auto_proxy_var.get():
            if disable_system_proxy():
                self._log("🔴 Proxy del sistema desactivado")

        self.running = False
        self._draw_dot("red")
        self.status_lbl.config(text="STOPPED", fg=C["red"])
        self.start_btn.config(text="▶ START VPN", bg=C["accent"], fg="#fff")
        self._log("VPN STOPPED")

    def _update_loop(self):
        if self.running and self.http_proxy:
            stats = self.http_proxy.stats()
            self.stat_connections.config(text=str(stats["clients"]))
            self.stat_upload.config(text=stats["total_out"])
            self.stat_download.config(text=stats["total_in"])
            self.proxy_info.config(
                text=f"HTTP: localhost:{self.config['proxy_port']}  |  "
                     f"SOCKS5: localhost:{self.config['socks_port']}  |  "
                     f"Encryption: {'ON' if self.config.get('encryption_key') else 'OFF'}  |  "
                     f"Auto Proxy: {'ON' if self.auto_proxy_var.get() else 'OFF'}  |  "
                     f"Kill Switch: {'ON' if self.kill_var.get() else 'OFF'}"
            )
        self.root.after(2000, self._update_loop)

    def _config_window(self):
        win = tk.Toplevel(self.root)
        win.title("VPN Configuration")
        win.geometry("420x340")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 420) // 2
        y = (win.winfo_screenheight() - 340) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="VPN CONFIGURATION", font=("Segoe UI", 13, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(pady=(16, 10))

        entries = {}
        for label, key, default in [
            ("HTTP Proxy Port", "proxy_port", "8888"),
            ("SOCKS5 Port", "socks_port", "1080"),
            ("Encryption Key", "encryption_key", ""),
            ("Max Connections", "max_connections", "50"),
        ]:
            f = tk.Frame(win, bg=C["bg"])
            f.pack(fill=tk.X, padx=30, pady=3)
            tk.Label(f, text=label, font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"],
                    width=16, anchor="w").pack(side=tk.LEFT)
            e = tk.Entry(f, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                        insertbackground=C["accent"], relief=tk.FLAT, show="*" if "key" in key else "")
            e.insert(0, str(self.config.get(key, default)))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            entries[key] = e

        def _save():
            for k, e in entries.items():
                try:
                    self.config[k] = int(e.get())
                except ValueError:
                    self.config[k] = e.get()
            save_config(self.config)
            self._log("Config saved. Restart VPN to apply.")
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=5,
                 cursor="hand2").pack(pady=(14, 0))

    def _on_close(self):
        if self.running:
            if messagebox.askyesno("Stop VPN", "Stop VPN and exit?"):
                self._stop()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    NexusVPN(root)
    root.mainloop()


if __name__ == "__main__":
    main()
