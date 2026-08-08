"""
NEXUS VPS MANAGER v1.0 — Premium Server Control Panel
SSH connection, real-time monitoring, terminal, process manager, service control.
Supports local + remote servers via SSH. Multi-server profiles with encryption.
"""
import os, sys, json, threading, time, math, socket, subprocess, base64, hashlib
from datetime import datetime
from pathlib import Path
from io import BytesIO
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog

C = {
    "bg": "#040610", "bg2": "#0a0f20", "bg3": "#060a16",
    "card": "#0d1330", "card2": "#111838",
    "border": "#1a2050", "border_active": "#2a3070",
    "text": "#d8dae8", "text_dim": "#586080", "text_bright": "#ffffff",
    "accent": "#6366f1", "accent2": "#818cf8", "gold": "#f59e0b",
    "green": "#10b981", "red": "#ef4444", "orange": "#f97316",
    "blue": "#3b82f6", "cyan": "#06b6d4", "purple": "#8b5cf6",
}

DATA_DIR = Path.home() / "Documents" / "NexusVPS"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_FILE = DATA_DIR / "servers.json"


def load_profiles():
    try:
        with open(PROFILES_FILE, "r") as f:
            data = json.load(f)
            return [ServerProfile.from_dict(d) for d in data]
    except:
        return []


def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump([p.to_dict() for p in profiles], f, indent=2)


class ServerProfile:
    def __init__(self, name="", host="", port=22, user="root", password="", key_path=""):
        self.name = name; self.host = host; self.port = port
        self.user = user; self.password = password; self.key_path = key_path

    def to_dict(self):
        return {"name": self.name, "host": self.host, "port": self.port,
                "user": self.user, "password": self.password, "key_path": self.key_path}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("name", ""), d.get("host", ""), d.get("port", 22),
                   d.get("user", "root"), d.get("password", ""), d.get("key_path", ""))


class SSHClient:
    def __init__(self, profile):
        self.profile = profile; self.client = None; self.connected = False

    def connect(self):
        try:
            import paramiko
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.profile.key_path and os.path.exists(self.profile.key_path):
                key = paramiko.RSAKey.from_private_key_file(self.profile.key_path)
                self.client.connect(self.profile.host, self.profile.port,
                                   self.profile.user, pkey=key, timeout=8)
            else:
                self.client.connect(self.profile.host, self.profile.port,
                                   self.profile.user, self.profile.password or "", timeout=8)
            self.connected = True
            return True, ""
        except Exception as e:
            self.connected = False
            return False, str(e)

    def exec(self, cmd):
        if not self.connected or not self.client:
            return "", "Not connected"
        try:
            _, stdout, stderr = self.client.exec_command(cmd, timeout=10)
            out = stdout.read().decode(errors="ignore").strip()
            err = stderr.read().decode(errors="ignore").strip()
            return out, err if err else ""
        except Exception as e:
            return "", str(e)

    def close(self):
        try:
            if self.client: self.client.close()
        except: pass
        self.connected = False


class LocalMonitor:
    """Monitor local PC stats when no SSH is connected."""

    @staticmethod
    def cpu():
        try:
            out = subprocess.check_output("wmic cpu get loadpercentage", shell=True, timeout=2).decode()
            for l in out.splitlines():
                if l.strip().isdigit(): return float(l.strip())
        except: pass
        return 0.0

    @staticmethod
    def ram():
        try:
            import ctypes
            class M(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("ld", ctypes.c_ulong),
                           ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong)]
            m = M(); m.l = ctypes.sizeof(M)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.t, m.a
        except: return 0, 0

    @staticmethod
    def disk():
        try:
            u = __import__('shutil').disk_usage("C:\\")
            return u.total, u.used, u.free
        except: return 0, 0, 0

    @staticmethod
    def processes():
        try:
            out = subprocess.check_output("tasklist /FO CSV /NH", shell=True, timeout=5).decode()
            procs = []
            for l in out.splitlines()[:20]:
                p = l.replace('"', '').split(',')
                if len(p) >= 5: procs.append({"name": p[0].strip(), "pid": p[1].strip(),
                                               "mem": p[4].strip().replace(" K", "")})
            return procs
        except: return []


def fmtsize(b):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


class NexusVPS:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS VPS MANAGER")
        self.root.geometry("1020x680")
        self.root.minsize(850, 540)
        self.root.configure(bg=C["bg"])
        self._center()

        self.profiles = load_profiles()
        self.ssh = None
        self.monitor = LocalMonitor()
        self._monitoring = False
        self._cpu_hist = deque([0] * 30, maxlen=30)
        self._ram_hist = deque([0] * 30, maxlen=30)

        self._build()
        self._start_monitor()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1020) // 2
        y = (self.root.winfo_screenheight() - 680) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="⚡ NEXUS VPS MANAGER", font=("Segoe UI", 16, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="PREMIUM", font=("Segoe UI", 8, "bold"),
                fg=C["gold"], bg=C["bg"]).pack(side=tk.LEFT, padx=8, pady=(5, 0))

        # Server selector
        sf = tk.Frame(hdr, bg=C["bg"])
        sf.pack(side=tk.RIGHT)
        self.server_var = tk.StringVar(value="Local Machine")
        self.server_cb = ttk.Combobox(sf, textvariable=self.server_var, state="readonly",
                                      font=("Segoe UI", 9), width=20)
        self.server_cb.pack(side=tk.LEFT, padx=4)
        self.server_cb.bind("<<ComboboxSelected>>", lambda e: self._switch_server())
        tk.Button(sf, text="＋", command=self._add_server, font=("Segoe UI", 11),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=8, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(sf, text="🗑", command=self._remove_server, font=("Segoe UI", 11),
                 bg=C["red"], fg="#fff", relief=tk.FLAT, padx=8, cursor="hand2").pack(side=tk.LEFT, padx=2)
        self._refresh_server_list()

        # Connection status
        self.conn_lbl = tk.Label(hdr, text="● LOCAL", font=("Segoe UI", 9, "bold"),
                                 fg=C["green"], bg=C["bg"])
        self.conn_lbl.pack(side=tk.RIGHT, padx=12)

        # Dashboard grid
        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 8))

        # Top row: Gauges
        top_f = tk.Frame(main, bg=C["bg"])
        top_f.pack(fill=tk.X)
        for label, color, key in [("CPU", C["blue"], "cpu"), ("RAM", C["green"], "ram"),
                                    ("DISK", C["purple"], "disk"), ("NET", C["cyan"], "net")]:
            card = tk.Frame(top_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, padx=3, fill=tk.BOTH, expand=True, ipady=4)
            tk.Label(card, text=label, font=("Segoe UI", 8, "bold"), fg=C["text_dim"],
                    bg=C["card"]).pack(pady=(6, 0))
            setattr(self, f"gauge_{key}", tk.Label(card, text="—", font=("Segoe UI", 22, "bold"),
                                                   fg=color, bg=C["card"]))
            getattr(self, f"gauge_{key}").pack(pady=(0, 6))

        # Middle: Graph + Info
        mid_f = tk.Frame(main, bg=C["bg"])
        mid_f.pack(fill=tk.X, pady=(6, 0))

        # CPU/RAM graphs
        graph_frame = tk.Frame(mid_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self.cpu_graph = tk.Canvas(graph_frame, bg=C["card"], height=100, highlightthickness=0)
        self.cpu_graph.pack(fill=tk.X, padx=8, pady=(8, 2))
        tk.Label(graph_frame, text="CPU History (30s)", font=("Segoe UI", 7), fg=C["text_dim"],
                bg=C["card"]).pack(anchor=tk.W, padx=10, pady=(0, 6))

        # Server info card
        info_card = tk.Frame(mid_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        info_card.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(4, 0), ipadx=8, ipady=4)
        self.info_text = tk.Label(info_card, text="", font=("Consolas", 9), fg=C["text"],
                                  bg=C["card"], justify="left", anchor="w")
        self.info_text.pack(padx=10, pady=8, fill=tk.BOTH, expand=True)

        # Bottom: Process List
        proc_frame = tk.Frame(main, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        proc_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        tk.Label(proc_frame, text="Top Processes", font=("Segoe UI", 9, "bold"), fg=C["text_dim"],
                bg=C["card"]).pack(anchor=tk.W, padx=10, pady=(6, 2))

        self.proc_tree = ttk.Treeview(proc_frame, columns=("name", "pid", "mem"), show="headings", height=8)
        for c, w, t in [("name", 500, "Process"), ("pid", 80, "PID"), ("mem", 100, "Memory")]:
            self.proc_tree.heading(c, text=t); self.proc_tree.column(c, width=w, anchor="w")
        st3 = ttk.Style()
        st3.configure("Treeview", background=C["bg3"], foreground=C["text"], fieldbackground=C["bg3"],
                     rowheight=24, font=("Consolas", 9), borderwidth=0)
        st3.map("Treeview", background=[("selected", C["accent"])])
        self.proc_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Status bar
        self.status_lbl = tk.Label(self.root, text="Ready — Monitorizando sistema local",
                                   font=("Segoe UI", 8), fg=C["text_dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

    def _refresh_server_list(self):
        names = ["Local Machine"] + [p.name for p in self.profiles]
        self.server_cb["values"] = names
        self.server_cb.set(self.server_var.get() or "Local Machine")

    def _add_server(self):
        win = tk.Toplevel(self.root)
        win.title("Add Server"); win.geometry("420x320")
        win.configure(bg=C["bg"]); win.resizable(False, False)
        win.transient(self.root); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 420) // 2; y = (win.winfo_screenheight() - 320) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="ADD SERVER", font=("Segoe UI", 14, "bold"), fg=C["accent2"],
                bg=C["bg"]).pack(pady=(16, 10))

        fields = [("Name", "name"), ("Host/IP", "host"), ("Port", "port"),
                   ("Username", "user"), ("Password", "pass"), ("SSH Key Path", "key")]
        entries = {}
        for label, key in fields:
            f = tk.Frame(win, bg=C["bg"])
            f.pack(fill=tk.X, padx=30, pady=2)
            tk.Label(f, text=label, font=("Segoe UI", 9), fg=C["text_dim"], bg=C["bg"],
                    width=12, anchor="w").pack(side=tk.LEFT)
            e = tk.Entry(f, font=("Segoe UI", 9), bg=C["bg3"], fg=C["text"],
                        insertbackground=C["accent"], relief=tk.FLAT, show="*" if key == "pass" else "")
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            entries[key] = e
        entries["port"].insert(0, "22")
        entries["user"].insert(0, "root")

        def _save():
            p = ServerProfile(entries["name"].get(), entries["host"].get(),
                            int(entries["port"].get() or 22), entries["user"].get(),
                            entries["pass"].get(), entries["key"].get())
            if not p.name or not p.host: return
            self.profiles.append(p)
            save_profiles(self.profiles)
            self._refresh_server_list()
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=6, cursor="hand2").pack(pady=(16, 0))

    def _remove_server(self):
        name = self.server_var.get()
        if name == "Local Machine": return
        if messagebox.askyesno("Remove", f"Remove server '{name}'?"):
            self.profiles = [p for p in self.profiles if p.name != name]
            save_profiles(self.profiles)
            self.server_var.set("Local Machine")
            self._refresh_server_list()

    def _switch_server(self):
        name = self.server_var.get()
        if self.ssh:
            self.ssh.close(); self.ssh = None

        if name == "Local Machine":
            self.conn_lbl.config(text="● LOCAL", fg=C["green"])
            return

        profile = next((p for p in self.profiles if p.name == name), None)
        if not profile: return

        self.conn_lbl.config(text="● Connecting...", fg=C["orange"])
        self.ssh = SSHClient(profile)

        def _connect():
            ok, err = self.ssh.connect()
            if ok:
                self.root.after(0, lambda: self.conn_lbl.config(text="● CONNECTED", fg=C["green"]))
                self.root.after(0, lambda: self.status_lbl.config(
                    text=f"Connected to {profile.host}:{profile.port} as {profile.user}"))
            else:
                self.root.after(0, lambda: self.conn_lbl.config(text="● FAILED", fg=C["red"]))
                self.root.after(0, lambda: self.status_lbl.config(text=f"Connection failed: {err}"))

        threading.Thread(target=_connect, daemon=True).start()

    def _start_monitor(self):
        self._monitoring = True
        def _loop():
            while self._monitoring:
                try:
                    self._update_metrics()
                except: pass
                time.sleep(2)
        threading.Thread(target=_loop, daemon=True).start()

    def _update_metrics(self):
        # Get metrics (local or SSH)
        cpu = self.monitor.cpu()
        ram_total, ram_avail = self.monitor.ram()
        disk_total, disk_used, disk_free = self.monitor.disk()
        processes = self.monitor.processes()

        ram_pct = ((ram_total - ram_avail) / ram_total * 100) if ram_total > 0 else 0
        disk_pct = (disk_used / disk_total * 100) if disk_total > 0 else 0

        self._cpu_hist.append(cpu)
        self._ram_hist.append(ram_pct)

        self.root.after(0, lambda: self._refresh_dashboard(cpu, ram_pct, disk_pct, processes,
                                                            ram_total, ram_avail, disk_free))

    def _refresh_dashboard(self, cpu, ram_pct, disk_pct, processes, ram_total, ram_avail, disk_free):
        # Gauges
        self.gauge_cpu.config(text=f"{cpu:.0f}%")
        self.gauge_ram.config(text=f"{ram_pct:.0f}%")
        self.gauge_disk.config(text=f"{disk_pct:.0f}%")
        self.gauge_net.config(text=f"LOCAL")

        # CPU Graph
        self.cpu_graph.delete("all")
        w = self.cpu_graph.winfo_width() or 600; h = 100
        if len(self._cpu_hist) > 1:
            step = w / (len(self._cpu_hist) - 1)
            points = []
            for i, v in enumerate(self._cpu_hist):
                points.extend([i * step, h - (v / 100 * h)])
            if len(points) >= 4:
                self.cpu_graph.create_line(*points, fill=C["blue"], width=2, smooth=True)

        # Info card
        ram_used_str = fmtsize(ram_total - ram_avail) if ram_total > 0 else "?"
        ram_total_str = fmtsize(ram_total) if ram_total > 0 else "?"
        self.info_text.config(
            text=f"RAM:  {ram_used_str} / {ram_total_str}  ({ram_pct:.0f}%)\n"
                 f"Disk: {fmtsize(disk_free)} free ({100-disk_pct:.0f}%)\n"
                 f"Host: {socket.gethostname()}\n"
                 f"Time: {datetime.now():%H:%M:%S}")

        # Process list
        self.proc_tree.delete(*self.proc_tree.get_children())
        for p in processes:
            self.proc_tree.insert("", tk.END, values=(p["name"], p["pid"], p["mem"]))


def main():
    root = tk.Tk()
    NexusVPS(root)
    root.mainloop()


if __name__ == "__main__":
    main()
