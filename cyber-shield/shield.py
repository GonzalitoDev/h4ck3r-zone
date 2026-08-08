"""
CYBERSHIELD v1.0 — Cybersecurity Scanner & Threat Detector
Scans: processes, startup, network, files, registry, browser, hosts, tasks, services.
Detects malware indicators, persistence mechanisms, and security weaknesses.
"""
import os, sys, json, threading, subprocess, re, socket, hashlib, time, winreg, fnmatch
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#06060c", "bg2": "#0e0e18", "bg3": "#08080f",
    "border": "#1e1e35", "text": "#e0e0e0", "dim": "#555568",
    "accent": "#7c3aed", "green": "#00e676", "red": "#ff1744",
    "orange": "#ff9100", "yellow": "#ffd740", "blue": "#448aff",
    "critical": "#ff1744", "high": "#ff5252", "medium": "#ff9100",
    "low": "#ffd740", "info": "#448aff",
}

HOME = Path.home()
APPDATA = os.environ.get("APPDATA", ""); LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
PROGRAMDATA = os.environ.get("PROGRAMDATA", "")

# ====== THREAT SIGNATURES ======
SUSPICIOUS_PROCESSES = [
    "keylogger", "stealer", "rat", "trojan", "miner", "crypto", "ransom",
    "injector", "packer", "dropper", "downloader", "backdoor", "exploit",
    "hacktool", "cracktool", "passwordrecovery", "pwdump", "mimikatz",
    "meterpreter", "shell", "bind", "reverse", "beacon", "payload",
    "darkcomet", "njrat", "nanocore", "asyncrat", "remcos", "agenttesla",
    "formbook", "lokibot", "hawkeye", "predator", "azovult", "vidar",
    "redline", "raccoon", "mars", "aurora", "xworm", "venom",
    "xmrig", "xmr", "cpuminer", "minergate", "nicehash", "phoenixminer",
    "lolminer", "t-rex", "gminer", "nbminer", "teamredminer",
    "wireshark", "nmap", "zenmap", "metasploit", "burpsuite", "sqlmap",
    "hydra", "john", "hashcat", "aircrack", "ettercap", "cain",
]
SUSPICIOUS_PORTS = [4444, 5555, 6666, 6667, 7777, 8080, 8443, 8888, 9000, 9001, 9999,
                    1337, 31337, 4782, 5800, 5900, 6000, 6660, 6697, 6969]
SUSPICIOUS_DOMAINS = ["no-ip", "duckdns", "ngrok", "serveo", "localtunnel",
                       "bit.ly", "tinyurl", "rebrand.ly", "0x", "pastebin"]
MALWARE_PERSISTENCE_KEYS = [
    r"Software\Microsoft\Windows\CurrentVersion\Run",
    r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
    r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
    r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon\Shell",
    r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit",
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    r"Software\Microsoft\Active Setup\Installed Components",
]
MALICIOUS_EXTENSIONS = ["adblock-genesis", "megasync", "search-marquis", "searchbaron",
                         "weknow", "cinemaplus", "hd-", "stream-", "findflarex"]
SUSPICIOUS_FILE_NAMES = [".exe", ".bat", ".ps1", ".vbs", ".js", ".hta", ".scr", ".pif",
                          ".dll", ".sys", ".jar"]
SUSPICIOUS_PATHS = [
    str(HOME / "AppData/Roaming/**/*.exe"),
    str(HOME / "AppData/Local/Temp/**/*.exe"),
    str(HOME / "Downloads/**/*.exe"),
    os.path.join(PROGRAMDATA, "**/*.exe") if PROGRAMDATA else "",
]


def run_cmd(cmd, timeout=10):
    try:
        return subprocess.check_output(cmd, shell=True, timeout=timeout,
                                       stderr=subprocess.DEVNULL).decode(errors="ignore").strip()
    except: return ""


# ====== SCANNERS ======
class ScanModule:
    def __init__(self, name, icon, description):
        self.name = name; self.icon = icon; self.description = description
        self.findings = []; self.scanned = False; self.threats = 0

    def add(self, name, description, severity, evidence="", fix=""):
        self.findings.append({"name": name, "desc": description, "sev": severity,
                              "evidence": evidence, "fix": fix})
        if severity in ("CRITICAL", "HIGH"): self.threats += 1


def scan_system_info():
    m = ScanModule("System Info", "🖥️", "Verifica estado de seguridad del sistema")
    try:
        defender = run_cmd('powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled"', 8)
        m.add("Windows Defender", "Estado del antivirus integrado de Windows",
              "INFO" if defender and "True" in defender else "HIGH",
              f"Defender activo: {defender or 'Desconocido'}",
              "Activar Windows Defender si está desactivado.")
    except: pass
    try:
        fw = run_cmd('netsh advfirewall show currentprofile state', 5)
        if "ON" in (fw or ""):
            m.add("Firewall activo", "El firewall de Windows está habilitado.", "INFO", fw[:100])
        else:
            m.add("Firewall desactivado", "El firewall de Windows no está activo.", "HIGH",
                  fw or "No se pudo verificar", "Activar el firewall de Windows.")
    except: pass
    try:
        updates = run_cmd('wmic qfe list brief', 5)
        if updates:
            m.add("Actualizaciones", "Windows Update tiene parches instalados.", "INFO", f"{len(updates.splitlines())} updates")
    except: pass
    m.scanned = True; return m


def scan_processes():
    m = ScanModule("Process Scanner", "⚙️", "Analiza procesos en ejecución")
    try:
        out = run_cmd('tasklist /FO CSV /NH', 10)
        for line in out.splitlines():
            parts = line.replace('"', '').split(',')
            if len(parts) < 5: continue
            name, pid = parts[0].strip(), parts[1].strip()
            name_l = name.lower()
            for s in SUSPICIOUS_PROCESSES:
                if s in name_l:
                    m.add(f"Proceso sospechoso: {name}", f"El proceso '{name}' (PID {pid}) coincide con firma '{s}'.",
                          "HIGH" if s in ["keylogger","stealer","trojan","ransom","miner","backdoor"] else "MEDIUM",
                          f"PID: {pid}, Nombre: {name}", "Investigar y terminar si no es legítimo.")
                    break
    except: pass
    m.scanned = True; return m


def scan_startup():
    m = ScanModule("Startup Scanner", "🚀", "Verifica programas de inicio")
    startup_paths = [
        os.path.join(APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
        os.path.join(PROGRAMDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
    ]
    for sp in startup_paths:
        if not os.path.exists(sp): continue
        for f in os.scandir(sp):
            try:
                name = f.name.lower()
                for s in SUSPICIOUS_PROCESSES:
                    if s in name:
                        m.add(f"Inicio sospechoso: {f.name}", f"Archivo '{f.name}' en carpeta de inicio coincide con '{s}'.",
                              "HIGH", str(f.path), "Mover a cuarentena y verificar.")
            except: pass

    # Registry startup
    for hkey_base, label, key in [(0x80000001, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run"),
                                    (0x80000002, "HKLM", r"Software\Microsoft\Windows\CurrentVersion\Run")]:
        try:
            k = winreg.OpenKey(hkey_base, key, 0, winreg.KEY_READ)
            for i in range(winreg.QueryInfoKey(k)[1]):
                try:
                    n, v, _ = winreg.EnumValue(k, i)
                    nl, vl = n.lower(), v.lower()
                    for s in SUSPICIOUS_PROCESSES:
                        if s in nl or s in vl:
                            m.add(f"Registro sospechoso ({label}): {n}",
                                  f"Entrada de inicio '{n} = {v[:80]}' coincide con '{s}'.",
                                  "HIGH" if s in ["trojan","ransom","keylogger","stealer"] else "MEDIUM",
                                  f"{label}\\Run: {n} = {v[:100]}", "Eliminar entrada del registro si no es legítimo.")
                except: pass
            winreg.CloseKey(k)
        except: pass
    m.scanned = True; return m


def scan_network():
    m = ScanModule("Network Scanner", "🌐", "Analiza conexiones de red activas")
    try:
        out = run_cmd('netstat -ano', 10)
        connections = []
        for line in out.splitlines():
            if not line.strip(): continue
            parts = line.split()
            if len(parts) < 5: continue
            proto, local, remote, state, pid = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                rport = int(remote.split(":")[-1]) if ":" in remote else 0
                r_host = remote.split(":")[0]
                if rport in SUSPICIOUS_PORTS:
                    connections.append(f"{proto} {local} -> {remote} ({state})")
                    m.add(f"Conexión a puerto sospechoso {rport}",
                          f"Conexión {proto} desde {local} hacia {remote} en puerto {rport}.",
                          "MEDIUM", f"PID: {pid}, Puerto: {rport}",
                          "Verificar el proceso con PID. Si no es legítimo, bloquear con firewall.")
                for dom in SUSPICIOUS_DOMAINS:
                    if dom in r_host.lower():
                        m.add(f"Conexión a dominio sospechoso: {r_host}",
                              f"Conexión {proto} a {remote} (contiene '{dom}').",
                              "HIGH", f"PID: {pid}, Dominio: {r_host}",
                              "Verificar el proceso y bloquear la conexión si es maliciosa.")
            except: pass
    except: pass
    m.scanned = True; return m


def scan_files():
    m = ScanModule("File Scanner", "📁", "Escanea archivos en ubicaciones críticas")
    paths_to_check = [
        (HOME / "Downloads", "Downloads"),
        (HOME / "AppData" / "Local" / "Temp", "Temp"),
        (HOME / "AppData" / "Roaming", "Roaming"),
    ]
    for base_path, label in paths_to_check:
        if not base_path.exists(): continue
        try:
            for root, dirs, files in os.walk(str(base_path)):
                # Limit depth
                depth = root.replace(str(base_path), "").count(os.sep)
                if depth > 2: continue
                for f in files:
                    fn = f.lower()
                    for s in SUSPICIOUS_PROCESSES:
                        if s in fn:
                            fp = os.path.join(root, f)
                            try:
                                sz = os.path.getsize(fp)
                                if sz < 50 * 1024 * 1024:  # Skip huge files
                                    m.add(f"Archivo sospechoso: {f}",
                                          f"Encontrado en {label}: {fp[-80:]} (coincide con '{s}')",
                                          "MEDIUM", f"{fp} ({sz} bytes)",
                                          "Verificar en VirusTotal. Mover a cuarentena si es malicioso.")
                            except: pass
                            break
        except Exception: pass

    # Check hosts file
    hosts_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "drivers", "etc", "hosts")
    if os.path.exists(hosts_path):
        try:
            with open(hosts_path, "r") as f:
                hosts_content = f.read().lower()
            redirects = []
            for line in hosts_content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    redirects.append(line)
            if len(redirects) > 5:
                m.add(f"Archivo hosts modificado ({len(redirects)} entradas)",
                      "El archivo hosts tiene múltiples redirecciones. Puede indicar secuestro DNS.",
                      "MEDIUM", f"{len(redirects)} redirects activos",
                      "Revisar entradas en C:\\Windows\\System32\\drivers\\etc\\hosts")
        except: pass

    m.scanned = True; return m


def scan_registry():
    m = ScanModule("Registry Scanner", "📋", "Verifica claves de persistencia de malware")

    # Check common persistence keys
    reg_checks = [
        (0x80000001, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run", "Startup (User)"),
        (0x80000002, "HKLM", r"Software\Microsoft\Windows\CurrentVersion\Run", "Startup (System)"),
        (0x80000002, "HKLM", r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Winlogon"),
        (0x80000001, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders", "Shell Folders"),
        (0x80000001, "HKCU", r"Software\Microsoft\Command Processor", "Command Processor"),
        (0x80000001, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "Policies"),
    ]
    for hbase, label, key, desc in reg_checks:
        try:
            k = winreg.OpenKey(hbase, key, 0, winreg.KEY_READ)
            count = winreg.QueryInfoKey(k)[1]
            if count > 10:
                m.add(f"Muchas entradas en {desc} ({label})",
                      f"Hay {count} entradas en {key}. Puede indicar malware persistence.",
                      "LOW", f"{label}: {count} entries",
                      "Revisar entradas manualmente con regedit.")
            winreg.CloseKey(k)
        except: pass

    # Check Autoruns disabled
    try:
        k = winreg.OpenKey(0x80000001, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
                          0, winreg.KEY_READ)
        disabled = winreg.QueryInfoKey(k)[1]
        if disabled > 0:
            m.add("Programas de inicio bloqueados", f"Windows ha bloqueado {disabled} programa(s) de inicio.",
                  "INFO", f"{disabled} disabled entries",
                  "Programas bloqueados por seguridad. Revisar en Administrador de Tareas > Inicio.")
        winreg.CloseKey(k)
    except: pass

    m.scanned = True; return m


def scan_browsers():
    m = ScanModule("Browser Scanner", "🌍", "Verifica extensiones y configuraciones del navegador")
    browsers = {
        "Chrome": os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(LOCALAPPDATA, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(LOCALAPPDATA, "BraveSoftware", "Brave-Browser", "User Data"),
    }
    for browser, bp in browsers.items():
        if not os.path.exists(bp): continue
        # Check extensions
        for root, dirs, files in os.walk(bp):
            if "Extensions" in root and root.count(os.sep) - bp.count(os.sep) > 1:
                for d in dirs:
                    for mal in MALICIOUS_EXTENSIONS:
                        if mal in d.lower():
                            m.add(f"Extensión maliciosa ({browser}): {d}",
                                  f"Extensión coincide con firma '{mal}'.", "HIGH",
                                  f"Extension ID: {d}",
                                  f"Eliminar extensión {d} de {browser}.")
                break

        # Check Preferences for hijacked search
        pref_file = os.path.join(bp, "Default", "Preferences")
        if os.path.exists(pref_file):
            try:
                with open(pref_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for mal in ["search-marquis", "searchbaron", "weknow", "findflarex"]:
                    if mal in content.lower():
                        m.add(f"Search hijack ({browser}): {mal}",
                              f"Buscador secuestrado detectado en {browser}.", "HIGH",
                              f"Keyword: {mal}",
                              "Restablecer configuración del navegador.")
            except: pass
    m.scanned = True; return m


def scan_tasks():
    m = ScanModule("Task Scanner", "📅", "Busca tareas programadas sospechosas")
    try:
        out = run_cmd('schtasks /query /FO CSV /NH', 15)
        for line in out.splitlines():
            if not line.strip(): continue
            parts = line.replace('"', '').split(',')
            if len(parts) < 2: continue
            task_name = parts[0].strip().lower()
            for s in SUSPICIOUS_PROCESSES:
                if s in task_name:
                    m.add(f"Tarea sospechosa: {parts[0].strip()}",
                          f"Tarea programada '{parts[0][:80]}' coincide con firma '{s}'.",
                          "MEDIUM", f"Task: {parts[0][:100]}",
                          "Revisar y eliminar en Task Scheduler si no es legítima.")
                    break
    except: pass
    m.scanned = True; return m


def scan_services():
    m = ScanModule("Service Scanner", "🔧", "Analiza servicios de Windows")
    try:
        out = run_cmd('sc query state= all', 15)
        current_service = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("SERVICE_NAME:"):
                current_service = line.split(":", 1)[1].strip().lower()
            if current_service:
                for s in SUSPICIOUS_PROCESSES:
                    if s in current_service:
                        m.add(f"Servicio sospechoso: {current_service}",
                              f"Servicio '{current_service}' coincide con firma '{s}'.",
                              "HIGH", f"Service: {current_service}",
                              "Detener y deshabilitar el servicio. Investigar origen.")
                        break
    except: pass
    m.scanned = True; return m


# ====== GUI ======
class CyberShield:
    def __init__(self, root):
        self.root = root
        self.root.title("CYBERSHIELD v1.0")
        self.root.geometry("960x660")
        self.root.minsize(780, 500)
        self.root.configure(bg=C["bg"])
        self._center()
        self.modules = []
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 960) // 2
        y = (self.root.winfo_screenheight() - 660) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=20, pady=(14, 0))
        tk.Label(hdr, text="🛡️ CYBERSHIELD", font=("Segoe UI", 18, "bold"),
                fg=C["accent"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="v1.0 | Cybersecurity Scanner", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Threat level indicator
        self.threat_frame = tk.Frame(hdr, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        self.threat_frame.pack(side=tk.RIGHT, padx=10)
        self.threat_lbl = tk.Label(self.threat_frame, text="SCAN TO CHECK", font=("Segoe UI", 10, "bold"),
                                   fg=C["dim"], bg=C["bg2"])
        self.threat_lbl.pack(padx=14, pady=6)

        # Action buttons
        btn_f = tk.Frame(self.root, bg=C["bg"])
        btn_f.pack(fill=tk.X, padx=20, pady=(8, 0))
        self.scan_btn = tk.Button(btn_f, text="🛡️ FULL SCAN", command=self._scan_all,
                                  font=("Segoe UI", 11, "bold"), bg=C["accent"], fg="#fff",
                                  relief=tk.FLAT, padx=24, pady=8, cursor="hand2")
        self.scan_btn.pack(side=tk.LEFT)
        tk.Button(btn_f, text="⚡ QUICK SCAN", command=self._quick_scan,
                 font=("Segoe UI", 10), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=16, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=6)
        tk.Button(btn_f, text="📄 EXPORT REPORT", command=self._export,
                 font=("Segoe UI", 10), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=16, pady=6, cursor="hand2").pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(btn_f, mode="indeterminate", length=150)
        self.status_lbl = tk.Label(btn_f, text="", font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.RIGHT, padx=8)

        # Results tree
        tf = tk.Frame(self.root, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 8))

        cols = ("sev", "module", "name", "evidence", "fix")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for c, w, t in [("sev", "!", 26), ("module", "Module", 110), ("name", "Finding", 260),
                         ("evidence", "Evidence", 280), ("fix", "Fix", 200)]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor="w")
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg3"], foreground=C["text"], fieldbackground=C["bg3"],
                     rowheight=26, font=("Segoe UI", 8), borderwidth=0)
        st2.map("Treeview", background=[("selected", C["accent"])])
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for s, c in {"CRITICAL": C["critical"], "HIGH": C["high"], "MEDIUM": C["medium"],
                      "LOW": C["low"], "INFO": C["info"]}.items():
            self.tree.tag_configure(s, foreground=c)

        # Filter bar
        flt = tk.Frame(self.root, bg=C["bg"])
        flt.pack(fill=tk.X, padx=20, pady=(0, 4))
        tk.Label(flt, text="Filter:", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT)
        self.fvars = {}
        for s, c in [("CRITICAL", C["critical"]), ("HIGH", C["high"]), ("MEDIUM", C["medium"]),
                      ("LOW", C["low"]), ("INFO", C["info"])]:
            v = tk.BooleanVar(value=True); self.fvars[s] = v
            tk.Checkbutton(flt, text=s, variable=v, command=self._filter, bg=C["bg"], fg=c,
                          selectcolor=C["bg3"], activebackground=C["bg"],
                          font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 8))

    def _scan_all(self):
        self._run_scan(full=True)

    def _quick_scan(self):
        self._run_scan(full=False)

    def _run_scan(self, full=True):
        self.tree.delete(*self.tree.get_children())
        self.scan_btn.config(text="⏳ SCANNING...", state=tk.DISABLED, bg=C["bg2"], fg=C["dim"])
        self.progress.pack(side=tk.RIGHT, padx=8)
        self.progress.start(8)
        self.modules = []

        scanners = [scan_system_info, scan_processes, scan_startup]
        if full:
            scanners += [scan_network, scan_files, scan_registry, scan_browsers, scan_tasks, scan_services]

        def _run():
            total_threats = 0
            for scanner in scanners:
                self.root.after(0, lambda s=scanner: self.status_lbl.config(
                    text=f"Scanning: {s.__name__[5:].replace('_',' ').title()}..."))
                try:
                    m = scanner()
                    self.modules.append(m)
                    total_threats += m.threats
                except Exception as e:
                    print(f"Scanner error: {e}")
            self.root.after(0, lambda: self._scan_done(total_threats))

        threading.Thread(target=_run, daemon=True).start()

    def _scan_done(self, total_threats):
        self.scan_btn.config(text="🛡️ FULL SCAN", state=tk.NORMAL, bg=C["accent"], fg="#fff")
        self.progress.stop(); self.progress.pack_forget()
        self._filter()

        if total_threats > 0:
            self.threat_lbl.config(text=f"⚠️ {total_threats} THREATS FOUND", fg=C["red"])
            self.threat_lbl.master.config(highlightbackground=C["red"])
        else:
            self.threat_lbl.config(text="✅ SYSTEM CLEAN", fg=C["green"])
            self.threat_lbl.master.config(highlightbackground=C["green"])

        total_findings = sum(len(m.findings) for m in self.modules)
        self.status_lbl.config(text=f"Done. {total_findings} findings. {total_threats} threats.")

    def _filter(self):
        self.tree.delete(*self.tree.get_children())
        for m in self.modules:
            for f in m.findings:
                if self.fvars.get(f["sev"], tk.BooleanVar(value=True)).get():
                    self.tree.insert("", tk.END, values=(
                        f["sev"][:3], m.name, f["name"],
                        f["evidence"][:120], f["fix"][:100]
                    ), tags=(f["sev"],))

    def _export(self):
        if not self.modules:
            messagebox.showinfo("No data", "Run a scan first.")
            return
        fp = tk.filedialog.asksaveasfilename(defaultextension=".html",
                                             filetypes=[("HTML", "*.html"), ("Text", "*.txt")],
                                             initialfile="cybershield_report.html")
        if not fp: return

        total_findings = sum(len(m.findings) for m in self.modules)
        total_threats = sum(m.threats for m in self.modules)

        if fp.endswith(".html"):
            html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>CyberShield Report</title>
<style>body{{background:#06060c;color:#e0e0e0;font-family:monospace;max-width:900px;margin:auto;padding:20px}}
h1{{color:#7c3aed;border-bottom:2px solid #1e1e35;padding-bottom:10px}}
.meta{{color:#555568;font-size:12px}}
.finding{{background:#0e0e18;border-left:4px solid #555;margin:8px 0;padding:12px;border-radius:4px}}
.crit{{border-left-color:#ff1744}}.high{{border-left-color:#ff5252}}.med{{border-left-color:#ff9100}}
.low{{border-left-color:#ffd740}}.info{{border-left-color:#448aff}}
.sev{{font-weight:bold;font-size:11px}}.name{{color:#fff;font-size:13px;font-weight:bold}}
.ev{{font-size:10px;color:#888;background:#08080f;padding:6px;margin:4px 0}}.fix{{font-size:11px;color:#00e676}}
</style></head><body>
<h1>CYBERSHIELD v1.0 — Report</h1>
<p class="meta">Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<p class="meta">Findings: {total_findings} | Threats: {total_threats}</p>
"""
            for m in self.modules:
                html += f'<h2>{m.icon} {m.name}</h2>'
                for f in m.findings:
                    cls = {"CRITICAL":"crit","HIGH":"high","MEDIUM":"med","LOW":"low","INFO":"info"}.get(f["sev"],"info")
                    html += f"""<div class="finding {cls}">
<div class="sev" style="color:{C.get(f['sev'].lower(),C['text'])}">{f['sev']}</div>
<div class="name">{f['name']}</div><div>{f['desc']}</div>
<div class="ev">{f['evidence']}</div><div class="fix">🔧 {f['fix']}</div></div>"""
            html += "</body></html>"
            with open(fp, "w", encoding="utf-8") as f: f.write(html)
        else:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"CYBERSHIELD v1.0 Report\n{'='*50}\nDate: {datetime.now().isoformat()}\n\n")
                for m in self.modules:
                    f.write(f"--- {m.icon} {m.name} ---\n")
                    for fd in m.findings:
                        f.write(f"[{fd['sev']}] {fd['name']}\n  {fd['desc']}\n  Evidence: {fd['evidence']}\n  Fix: {fd['fix']}\n\n")
        messagebox.showinfo("Exported", f"Report saved to:\n{fp}")


def main():
    root = tk.Tk()
    CyberShield(root)
    root.mainloop()


if __name__ == "__main__":
    main()
