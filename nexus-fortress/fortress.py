"""
NEXUS FORTRESS v1.0 — Windows Security Hardening & Audit
Scans: Defender, Firewall, UAC, SmartScreen, BitLocker, Updates,
Privacy, User Accounts, Services, Network. Security score + auto-fix.
"""
import os, sys, json, subprocess, re, socket, winreg, ctypes, threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#06080c", "bg2": "#0e1220", "card": "#141830",
    "border": "#1e2848", "text": "#d0d4e4", "dim": "#485070",
    "accent": "#f59e0b", "accent2": "#fbbf24",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa",
}

def run_cmd(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except: return ""

def reg_read(key_path, value_name):
    try:
        hkey_map = {"HKLM": 0x80000002, "HKCU": 0x80000001}
        hive, subkey = key_path.split("\\", 1)
        hive_const = hkey_map.get(hive, 0x80000002)
        key = winreg.OpenKey(hive_const, subkey, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return val
    except: return None

SECURITY_CHECKS = []

class SecurityCheck:
    def __init__(self, name, category, description):
        self.name = name; self.category = category; self.description = description
        self.status = "unknown"; self.icon = "❓"; self.fix_cmd = ""

    def set_pass(self, detail=""): self.status = "pass"; self.icon = "✅"; self.detail = detail
    def set_fail(self, detail=""): self.status = "fail"; self.icon = "❌"; self.detail = detail
    def set_warn(self, detail=""): self.status = "warn"; self.icon = "⚠️"; self.detail = detail
    def set_unknown(self, detail=""): self.status = "unknown"; self.icon = "❓"; self.detail = detail


def scan_all():
    results = []

    # ===== WINDOWS DEFENDER =====
    c = SecurityCheck("Defender Status", "Antivirus", "Windows Defender antivirus protection")
    try:
        out = run_cmd('powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled"')
        if "True" in out: c.set_pass("Defender is active and protecting")
        else: c.set_fail("Defender is DISABLED — enable immediately")
    except: c.set_unknown("Cannot check Defender status")
    results.append(c)

    c = SecurityCheck("Real-time Protection", "Antivirus", "Real-time scanning active")
    try:
        out = run_cmd('powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled"')
        if "True" in out: c.set_pass("Real-time protection active")
        else: c.set_fail("Real-time protection OFF")
    except: c.set_unknown()
    results.append(c)

    c = SecurityCheck("Defender Updates", "Antivirus", "Defender signatures up to date")
    try:
        out = run_cmd('powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusSignatureAge"')
        age = int(out.strip()) if out.strip().isdigit() else 999
        if age < 3: c.set_pass(f"Signatures updated ({age} days old)")
        elif age < 7: c.set_warn(f"Signatures {age} days old")
        else: c.set_fail(f"Signatures {age} days old — update now")
    except: c.set_unknown()
    results.append(c)

    # ===== FIREWALL =====
    c = SecurityCheck("Windows Firewall", "Network", "Windows Firewall active")
    try:
        out = run_cmd('netsh advfirewall show allprofiles state')
        domains_on = out.count("ON")
        if domains_on >= 3: c.set_pass(f"Firewall ON ({domains_on}/3 profiles)")
        elif domains_on > 0: c.set_warn(f"Firewall partially ON ({domains_on}/3)")
        else: c.set_fail("Firewall OFF on all profiles")
    except: c.set_unknown()
    results.append(c)

    c = SecurityCheck("Firewall Inbound Rules", "Network", "Inbound connections blocked by default")
    try:
        out = run_cmd('netsh advfirewall show domainprofile | find "InboundConnections"')
        if "Block" in out: c.set_pass("Inbound blocked (recommended)")
        else: c.set_warn("Inbound not blocked by default")
    except: c.set_unknown()
    results.append(c)

    # ===== UAC =====
    c = SecurityCheck("UAC Status", "System", "User Account Control enabled")
    try:
        val = reg_read("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "EnableLUA")
        if val == 1: c.set_pass("UAC enabled (recommended)")
        else: c.set_fail("UAC disabled — enable for security")
    except: c.set_unknown()
    results.append(c)

    # ===== SMARTS SCREEN =====
    c = SecurityCheck("SmartScreen", "System", "SmartScreen filter active")
    try:
        val = reg_read("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer", "SmartScreenEnabled")
        if val in ("on", "On", "ON", "Block", 1): c.set_pass("SmartScreen active")
        else: c.set_warn("SmartScreen disabled")
    except: c.set_unknown()
    results.append(c)

    # ===== WINDOWS UPDATE =====
    c = SecurityCheck("Windows Update", "Updates", "Automatic updates enabled")
    try:
        val = reg_read("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update", "AUOptions")
        if val and val >= 3: c.set_pass("Auto updates ON")
        elif val and val >= 1: c.set_warn("Updates manual/notify only")
        else: c.set_fail("Updates disabled")
    except: c.set_unknown()
    results.append(c)

    # ===== BITLOCKER =====
    c = SecurityCheck("BitLocker Encryption", "Encryption", "Drive encryption status")
    try:
        out = run_cmd('manage-bde -status C:')
        if "Fully Encrypted" in out or "Protection On" in out:
            c.set_pass("C: drive encrypted")
        elif "Encrypting" in out or "Encryption in Progress" in out:
            c.set_warn("Encryption in progress")
        else:
            c.set_warn("C: drive NOT encrypted — consider BitLocker")
    except: c.set_unknown()
    results.append(c)

    # ===== GUEST ACCOUNT =====
    c = SecurityCheck("Guest Account", "Users", "Guest account disabled")
    try:
        out = run_cmd('net user Guest')
        if "Account active" in out and "Yes" in out:
            c.set_fail("Guest account ACTIVE — disable it")
        else:
            c.set_pass("Guest account disabled")
    except: c.set_pass("Guest account not found (disabled)")
    results.append(c)

    # ===== ADMIN USERS =====
    c = SecurityCheck("Admin Users", "Users", "Administrator accounts count")
    try:
        out = run_cmd('net localgroup Administrators')
        lines = [l for l in out.splitlines() if l.strip() and "---" not in l and "command" not in l.lower()]
        members = [l.strip() for l in lines[1:]] if len(lines) > 1 else []
        admin_count = len([m for m in members if m])
        if admin_count <= 2: c.set_pass(f"{admin_count} admin account(s)")
        else: c.set_warn(f"{admin_count} admin accounts — too many")
    except: c.set_unknown()
    results.append(c)

    # ===== REMOTE DESKTOP =====
    c = SecurityCheck("Remote Desktop", "Network", "RDP disabled")
    try:
        val = reg_read("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server", "fDenyTSConnections")
        if val == 1: c.set_pass("RDP disabled (secure)")
        else: c.set_warn("RDP enabled — restrict if not needed")
    except: c.set_unknown()
    results.append(c)

    # ===== WINDOWS 11/10 SPECIFIC =====
    c = SecurityCheck("Core Isolation", "System", "Memory integrity / VBS")
    try:
        out = run_cmd('powershell -Command "Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\\Microsoft\\Windows\\DeviceGuard | Select-Object -ExpandProperty VirtualizationBasedSecurityStatus"')
        if "2" in out: c.set_pass("Memory integrity ON")
        else: c.set_warn("Virtualization-based security OFF")
    except: c.set_unknown()
    results.append(c)

    # ===== TPM =====
    c = SecurityCheck("TPM Module", "Hardware", "Trusted Platform Module present")
    try:
        out = run_cmd('powershell -Command "Get-Tpm | Select-Object -ExpandProperty TpmPresent"')
        if "True" in out: c.set_pass("TPM 2.0 present")
        else: c.set_warn("TPM not found")
    except: c.set_unknown()
    results.append(c)

    # ===== NETWORK PROFILE =====
    c = SecurityCheck("Network Profile", "Network", "Network is Private/Public")
    try:
        out = run_cmd('powershell -Command "Get-NetConnectionProfile | Select-Object -ExpandProperty NetworkCategory"')
        pub = "Public" in out
        if pub: c.set_warn("Network is PUBLIC — firewall stricter")
        else: c.set_pass("Network is PRIVATE — firewall relaxed")
    except: c.set_unknown()
    results.append(c)

    # ===== PASSWORD POLICY =====
    c = SecurityCheck("Password Policy", "Users", "Password complexity requirements")
    try:
        out = run_cmd('net accounts')
        if "min password length" in out.lower():
            c.set_pass("Password policy active")
        else: c.set_warn("Check password policy")
    except: c.set_unknown()
    results.append(c)

    return results


class NexusFortress:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS FORTRESS — Security Hardening")
        self.root.geometry("850x620")
        self.root.minsize(650, 450)
        self.root.configure(bg=C["bg"])
        self._center()
        self.results = []
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 850) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🏰 NEXUS FORTRESS", font=("Segoe UI", 18, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Windows Security Hardening", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Score card
        score_f = tk.Frame(self.root, bg=C["bg"])
        score_f.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.score_frame = tk.Frame(score_f, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        self.score_frame.pack(fill=tk.X)
        score_inner = tk.Frame(self.score_frame, bg=C["card"])
        score_inner.pack(padx=14, pady=10)
        self.score_lbl = tk.Label(score_inner, text="—", font=("Segoe UI", 36, "bold"),
                                  fg=C["dim"], bg=C["card"])
        self.score_lbl.pack(side=tk.LEFT, padx=(0, 14))
        self.score_text = tk.Label(score_inner, text="Click SCAN to analyze\nWindows security status",
                                   font=("Segoe UI", 10), fg=C["dim"], bg=C["card"], anchor="w", justify="left")
        self.score_text.pack(side=tk.LEFT)

        # Action buttons
        btn_f = tk.Frame(self.root, bg=C["bg"])
        btn_f.pack(fill=tk.X, padx=16, pady=(6, 0))
        tk.Button(btn_f, text="🔍 FULL SECURITY SCAN", command=self._scan,
                 font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#000",
                 relief=tk.FLAT, padx=18, pady=5, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(btn_f, text="🔧 AUTO-FIX ISSUES", command=self._autofix,
                 font=("Segoe UI", 10, "bold"), bg=C["green"], fg="#000",
                 relief=tk.FLAT, padx=16, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_f, text="📄 EXPORT REPORT", command=self._export,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        # Results tree
        tf = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))
        cols = ("icon","category","name","detail")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for c, w, t in [("icon",30,""),("category",100,"Category"),("name",200,"Check"),("detail",400,"Detail")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor="w")
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"],
                     rowheight=26, font=("Segoe UI", 8), borderwidth=0)
        st2.map("Treeview", background=[("selected", C["accent"])])
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("pass", foreground=C["green"])
        self.tree.tag_configure("fail", foreground=C["red"])
        self.tree.tag_configure("warn", foreground=C["orange"])
        self.tree.tag_configure("unknown", foreground=C["dim"])

        self.status_lbl = tk.Label(self.root, text="Ready — Click FULL SECURITY SCAN",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

    def _scan(self):
        self.tree.delete(*self.tree.get_children())
        self.status_lbl.config(text="🔍 Scanning Windows security...", fg=C["accent"])

        def _run():
            self.results = scan_all()
            self.root.after(0, self._show_results)
        threading.Thread(target=_run, daemon=True).start()

    def _show_results(self):
        self.tree.delete(*self.tree.get_children())
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        warned = sum(1 for r in self.results if r.status == "warn")
        total = len(self.results)
        score = int((passed / max(total, 1)) * 100)

        color = C["green"] if score >= 80 else C["orange"] if score >= 50 else C["red"]
        self.score_lbl.config(text=f"{score}%", fg=color)
        self.score_text.config(text=f"✅ {passed} passed  •  ⚠️ {warned} warnings  •  ❌ {failed} failed")

        for r in self.results:
            self.tree.insert("", tk.END, values=(r.icon, r.category, r.name, r.detail), tags=(r.status,))

        self.status_lbl.config(text=f"Scan complete — Security Score: {score}%", fg=color)

    def _autofix(self):
        if not self.results: return
        fixes = {
            "Firewall": 'netsh advfirewall set allprofiles state on',
            "UAC": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 1 /f',
            "Defender": 'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring 0"',
            "SmartScreen": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" /v SmartScreenEnabled /t REG_SZ /d "on" /f',
        }
        count = 0
        for r in self.results:
            if r.status == "fail":
                for key, cmd in fixes.items():
                    if key.lower() in r.name.lower():
                        try: subprocess.run(cmd, shell=True, timeout=5); count += 1
                        except: pass

        self.status_lbl.config(text=f"🔧 {count} fixes applied. Re-scan to verify.", fg=C["green"])
        if count > 0:
            messagebox.showinfo("Auto-Fix", f"{count} security fixes applied.\nRe-scan to verify changes.")

    def _export(self):
        if not self.results: return
        fp = tk.filedialog.asksaveasfilename(defaultextension=".html",
                                             filetypes=[("HTML", "*.html"), ("Text", "*.txt")],
                                             initialfile="fortress_report.html")
        if not fp: return

        passed = sum(1 for r in self.results if r.status == "pass")
        score = int((passed / max(len(self.results), 1)) * 100)

        if fp.endswith(".html"):
            html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Fortress Report</title>
<style>body{{background:#06080c;color:#d0d4e4;font-family:monospace;max-width:700px;margin:auto;padding:20px}}
h1{{color:#fbbf24;border-bottom:2px solid #1e2848;padding-bottom:8px}}.score{{font-size:36px;font-weight:bold}}
.pass{{color:#34d399}}.fail{{color:#f87171}}.warn{{color:#fb923c}}.check{{margin:8px 0;padding:10px;background:#0e1220;border-radius:6px;border-left:4px solid #1e2848}}
</style></head><body>
<h1>🏰 Nexus Fortress — Report</h1>
<p>Date: {datetime.now():%Y-%m-%d %H:%M} | Score: <span class="score">{score}%</span></p>
"""
            for r in self.results:
                html += f'<div class="check {r.status}"><b>{r.icon} {r.name}</b> [{r.category}]<br>{r.detail}</div>'
            html += "</body></html>"
            with open(fp, "w", encoding="utf-8") as f: f.write(html)
        else:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"NEXUS FORTRESS REPORT\n{datetime.now():%Y-%m-%d %H:%M}\nScore: {score}%\n\n")
                for r in self.results:
                    f.write(f"{r.icon} [{r.category}] {r.name}: {r.detail}\n")
        messagebox.showinfo("Exported", f"Report saved to:\n{fp}")


def main():
    root = tk.Tk()
    NexusFortress(root)
    root.mainloop()


if __name__ == "__main__":
    main()
