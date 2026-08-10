"""
NEXUS WEBSOCKET PRO v1.0 — Real-time WebSocket Server + Monitor
Built-in WebSocket server with client dashboard. Monitor connections,
broadcast messages, view live traffic. No external dependencies.
"""
import os, sys, json, threading, time, hashlib, base64, struct, socket, select
from datetime import datetime
from pathlib import Path
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#08080f", "bg2": "#101020", "card": "#181835",
    "border": "#202050", "text": "#d0d0e8", "dim": "#484878",
    "accent": "#06b6d4", "accent2": "#22d3ee",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa",
}

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def compute_accept(key):
    sha1 = hashlib.sha1((key + GUID).encode()).digest()
    return base64.b64encode(sha1).decode()


def create_frame(data, opcode=1):
    """Create WebSocket text frame."""
    if isinstance(data, str):
        data = data.encode()
    length = len(data)
    frame = bytearray()
    frame.append(0x80 | opcode)

    if length < 126:
        frame.append(length)
    elif length < 65536:
        frame.append(126)
        frame.extend(struct.pack(">H", length))
    else:
        frame.append(127)
        frame.extend(struct.pack(">Q", length))

    frame.extend(data)
    return bytes(frame)


def parse_frame(data):
    """Parse WebSocket frame. Returns (opcode, payload, is_final)."""
    if len(data) < 2:
        return None, None, False

    first = data[0]
    second = data[1]
    opcode = first & 0x0F
    is_final = bool(first & 0x80)
    masked = bool(second & 0x80)
    length = second & 0x7F
    offset = 2

    if length == 126:
        if len(data) < 4: return None, None, False
        length = struct.unpack(">H", data[2:4])[0]
        offset = 4
    elif length == 127:
        if len(data) < 10: return None, None, False
        length = struct.unpack(">Q", data[2:10])[0]
        offset = 10

    mask_key = None
    if masked:
        if len(data) < offset + 4: return None, None, False
        mask_key = data[offset:offset + 4]
        offset += 4

    if len(data) < offset + length: return None, None, False
    payload = bytearray(data[offset:offset + length])

    if mask_key:
        for i in range(len(payload)):
            payload[i] ^= mask_key[i % 4]

    return opcode, bytes(payload), is_final


class WSClient:
    def __init__(self, sock, addr, server):
        self.sock = sock
        self.addr = addr
        self.server = server
        self.connected = True
        self.handshake_done = False
        self.buffer = b""

    def handshake(self, data):
        text = data.decode(errors="ignore")
        key = None
        for line in text.split("\r\n"):
            if line.lower().startswith("sec-websocket-key:"):
                key = line.split(":", 1)[1].strip()
                break
        if key:
            accept = compute_accept(key)
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            )
            self.sock.sendall(response.encode())
            self.handshake_done = True
            return True
        return False

    def send(self, message):
        try:
            self.sock.sendall(create_frame(message))
        except:
            self.connected = False

    def close(self):
        try:
            self.sock.sendall(create_frame(b"", 0x08))
            self.sock.close()
        except:
            pass
        self.connected = False


class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=9001, callback=None):
        self.host = host
        self.port = port
        self.callback = callback
        self.running = False
        self.socket = None
        self.clients = []
        self.total_messages = 0
        self.total_connections = 0
        self.message_log = deque(maxlen=200)

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(100)
            self.running = True
            threading.Thread(target=self._loop, daemon=True).start()
            self._emit("server", f"Server started on ws://{self.host}:{self.port}")
            return True, ""
        except Exception as e:
            return False, str(e)

    def stop(self):
        self.running = False
        for c in self.clients[:]:
            c.close()
        if self.socket:
            try: self.socket.close()
            except: pass
        self._emit("server", "Server stopped")

    def _loop(self):
        while self.running:
            try:
                client_sock, addr = self.socket.accept()
                client = WSClient(client_sock, addr, self)
                self.clients.append(client)
                self.total_connections += 1
                self._emit("connect", f"New client: {addr[0]}:{addr[1]}")
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self._emit("error", str(e))

    def _handle_client(self, client):
        try:
            client.sock.settimeout(0.5)
            while self.running and client.connected:
                try:
                    data = client.sock.recv(65536)
                    if not data:
                        break
                except socket.timeout:
                    continue

                if not client.handshake_done:
                    if client.handshake(data):
                        continue
                    else:
                        break

                client.buffer += data
                while len(client.buffer) >= 2:
                    opcode, payload, is_final = parse_frame(client.buffer)
                    if payload is None:
                        break

                    frame_length = len(client.buffer) - len(client.buffer) + 2
                    if isinstance(payload, bytes):
                        client.buffer = client.buffer[frame_length + len(payload):]

                    if opcode == 0x08:
                        client.connected = False
                        break
                    elif opcode == 0x09:
                        client.sock.sendall(create_frame(b"", 0x0A))
                    elif opcode in (1, 2):
                        msg = payload.decode(errors="ignore") if opcode == 1 else str(payload)
                        self.total_messages += 1
                        self.message_log.append({
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "from": f"{client.addr[0]}:{client.addr[1]}",
                            "msg": msg[:200],
                            "direction": "received",
                        })
                        self._emit("message", f"{client.addr[0]}:{client.addr[1]} → {msg[:100]}")

                        # Echo back
                        try:
                            client.send(f"Server received: {msg}")
                        except:
                            pass
        except Exception as e:
            pass
        finally:
            client.close()
            if client in self.clients:
                self.clients.remove(client)
            self._emit("disconnect", f"Client disconnected: {client.addr[0]}:{client.addr[1]}")

    def broadcast(self, message):
        for c in self.clients[:]:
            if c.connected and c.handshake_done:
                try:
                    c.send(message)
                except:
                    c.connected = False
        self._emit("broadcast", f"Broadcast sent: {message[:80]}")

    def _emit(self, event_type, message):
        if self.callback:
            self.callback(event_type, message)


class NexusWS:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS WEBSOCKET PRO")
        self.root.geometry("900x620")
        self.root.minsize(650, 450)
        self.root.configure(bg=C["bg"])
        self._center()

        self.server = None
        self.running = False
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 900) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🔌 NEXUS WEBSOCKET PRO", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Real-time Server + Monitor", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Status
        sf = tk.Frame(hdr, bg=C["bg"]); sf.pack(side=tk.RIGHT)
        self.status_dot = tk.Canvas(sf, width=12, height=12, bg=C["bg"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT); self._draw_dot("red")
        self.status_lbl = tk.Label(sf, text="STOPPED", font=("Segoe UI", 9, "bold"),
                                   fg=C["red"], bg=C["bg"])
        self.status_lbl.pack(side=tk.LEFT, padx=4)

        # Control bar
        ctrl = tk.Frame(self.root, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=16, pady=(6, 0))
        self.start_btn = tk.Button(ctrl, text="▶ START SERVER", command=self._toggle,
                                   font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#000",
                                   relief=tk.FLAT, padx=18, pady=5, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT)
        tk.Label(ctrl, text="Puerto:", font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=(12, 4))
        self.port_var = tk.StringVar(value="9001")
        tk.Spinbox(ctrl, from_=1024, to=65535, textvariable=self.port_var, width=6,
                  font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT).pack(side=tk.LEFT)

        # Broadcast
        self.broadcast_e = tk.Entry(ctrl, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                                    insertbackground=C["accent"], relief=tk.FLAT, width=25)
        self.broadcast_e.pack(side=tk.RIGHT, ipady=2)
        self.broadcast_e.bind("<Return>", lambda e: self._broadcast())
        tk.Button(ctrl, text="📢 Broadcast", command=self._broadcast,
                 font=("Segoe UI", 9), bg=C["blue"], fg="#fff", relief=tk.FLAT,
                 padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT, padx=4)

        # Stats
        stats_f = tk.Frame(self.root, bg=C["bg"])
        stats_f.pack(fill=tk.X, padx=16, pady=(4, 0))
        for label, color in [("Clients", C["green"]), ("Messages", C["accent"]),
                              ("Total Conns", C["blue"]), ("Uptime", C["gold"])]:
            card = tk.Frame(stats_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True, ipady=4)
            tk.Label(card, text=label, font=("Segoe UI", 7, "bold"), fg=C["dim"], bg=C["card"]).pack(pady=(4, 0))
            key = label.lower().replace(" ", "_")
            setattr(self, f"stat_{key}", tk.Label(card, text="—",
                                                   font=("Segoe UI", 16, "bold"), fg=color, bg=C["card"]))
            getattr(self, f"stat_{key}").pack(pady=(0, 4))

        # Connection URL
        url_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        url_f.pack(fill=tk.X, padx=16, pady=(4, 0), ipady=4)
        self.url_lbl = tk.Label(url_f, text="ws://localhost:9001", font=("Consolas", 10, "bold"),
                                fg=C["green"], bg=C["card"])
        self.url_lbl.pack(padx=12, pady=6, anchor="w")

        # Message log
        tk.Label(self.root, text="LIVE MESSAGE LOG", font=("Segoe UI", 9, "bold"),
                fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=16, pady=(6, 2))
        log_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        log_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        # Console for live messages
        self.log_text = scrolledtext.ScrolledText(log_f, bg=C["bg2"], fg=C["text"],
                                                   font=("Consolas", 9), wrap=tk.WORD,
                                                   relief=tk.FLAT, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Color tags
        self.log_text.tag_configure("connect", foreground=C["green"])
        self.log_text.tag_configure("disconnect", foreground=C["red"])
        self.log_text.tag_configure("message", foreground=C["accent2"])
        self.log_text.tag_configure("broadcast", foreground=C["blue"])
        self.log_text.tag_configure("server", foreground=C["gold"])
        self.log_text.tag_configure("error", foreground=C["red"])

        self._update_loop()

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
        try:
            port = int(self.port_var.get())
        except:
            port = 9001

        self.server = WebSocketServer(port=port, callback=self._on_event)
        ok, err = self.server.start()

        if ok:
            self.running = True
            self._draw_dot("green")
            self.status_lbl.config(text="RUNNING", fg=C["green"])
            self.start_btn.config(text="⏹ STOP", bg=C["red"], fg="#fff")
            self.url_lbl.config(text=f"ws://localhost:{port}")
            self._log("▶ Server started", "server")
            self._log(f"Connect to: ws://localhost:{port}", "server")
            self._log(f"JavaScript: new WebSocket('ws://localhost:{port}')", "server")
            self._log("=" * 40, "server")
        else:
            self._log(f"Error: {err}", "error")

    def _stop(self):
        if self.server:
            self.server.stop()
            self.server = None
        self.running = False
        self._draw_dot("red")
        self.status_lbl.config(text="STOPPED", fg=C["red"])
        self.start_btn.config(text="▶ START SERVER", bg=C["accent"], fg="#000")
        self._log("■ Server stopped", "server")

    def _broadcast(self):
        msg = self.broadcast_e.get().strip()
        if not msg or not self.server:
            return
        self.server.broadcast(msg)
        self.broadcast_e.delete(0, tk.END)

    def _on_event(self, event_type, message):
        self.root.after(0, lambda: self._log(message, event_type))

    def _log(self, msg, tag=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        tags = tag if tag else "server"
        self.log_text.insert(tk.END, f"[{timestamp}] ", "server")
        self.log_text.insert(tk.END, f"{msg}\n", tags)
        self.log_text.see(tk.END)

    def _update_loop(self):
        if self.running and self.server:
            self.stat_clients.config(text=str(len(self.server.clients)))
            self.stat_messages.config(text=str(self.server.total_messages))
            self.stat_total_conns.config(text=str(self.server.total_connections))
        self.root.after(1000, self._update_loop)


def main():
    root = tk.Tk()
    NexusWS(root)
    root.mainloop()


if __name__ == "__main__":
    main()
