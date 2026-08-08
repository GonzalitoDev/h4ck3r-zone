"""
NETGUARD v1.0 — WiFi Network Security Scanner & Device Manager
Scans local network, discovers all connected devices, ports, MAC vendors.
Network security analysis, device identification, ARP scanning.
"""
import os, sys, json, threading, subprocess, socket, struct, re, time, ipaddress
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#060c10", "bg2": "#0c1620", "card": "#101e2d",
    "border": "#1a3050", "text": "#d0dae4", "dim": "#3d5570",
    "accent": "#06b6d4", "accent2": "#22d3ee",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa", "purple": "#a78bfa",
}

DATA_DIR = Path.home() / "Documents" / "NetGuard"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Common MAC vendor prefixes (first 6 hex chars)
MAC_VENDORS = {
    "000000": "Xerox", "000001": "Xerox", "00000C": "Cisco", "00001B": "Novell",
    "00001C": "Cisco", "00001D": "Cisco", "00001E": "Cisco", "00001F": "Cisco",
    "000020": "Cisco", "000021": "Cisco", "000022": "Cisco", "000023": "Cisco",
    "000024": "Cisco", "000025": "Cisco", "000026": "Cisco", "000027": "Cisco",
    "000028": "Cisco", "000029": "Cisco", "001122": "Apple", "0011CA": "Apple",
    "001B63": "Apple", "001CB3": "Apple", "001D4F": "Apple", "001E52": "Apple",
    "001EC2": "Apple", "001F5B": "Apple", "001FF3": "Apple", "0021E9": "Apple",
    "002312": "Apple", "0023DF": "Apple", "002436": "Apple", "002500": "Apple",
    "00254B": "Apple", "0025BC": "Apple", "002608": "Apple", "00264A": "Apple",
    "0026B0": "Apple", "0026BB": "Apple", "003065": "Apple", "0030F2": "Apple",
    "003EE1": "Apple", "0050C2": "Apple", "0050E4": "Apple", "0056CD": "Apple",
    "0070DE": "Apple", "008865": "Apple", "00A040": "Apple", "00A0D1": "Apple",
    "00B362": "Apple", "00C610": "Apple", "085700": "Apple", "0C3021": "Apple",
    "0C3E9F": "Apple", "0C4DE9": "Apple", "0C5101": "Apple", "1078D2": "Apple",
    "109ADD": "Apple", "10DD41": "Apple", "14109E": "Apple", "14BD61": "Apple",
    "1C1AC0": "Apple", "1C36BB": "Apple", "1C9148": "Apple", "2078F0": "Apple",
    "24A074": "Apple", "280BC0": "Apple", "2837E1": "Apple", "285AEB": "Apple",
    "3429A9": "Xiaomi", "34987E": "Xiaomi", "384B76": "Xiaomi", "409B28": "Xiaomi",
    "4434C0": "Xiaomi", "48215D": "Xiaomi", "4C49E3": "Xiaomi", "4C63EB": "Xiaomi",
    "50294A": "Xiaomi", "5894E5": "Xiaomi", "604A1C": "Xiaomi", "640980": "Xiaomi",
    "B0E235": "Xiaomi", "CC4B73": "Xiaomi", "D4959B": "Xiaomi", "E0B94D": "Xiaomi",
    "F09E63": "Xiaomi", "F49E61": "Xiaomi", "F894C2": "Xiaomi", "FCAB9A": "Xiaomi",
    "D0176A": "Samsung", "D8D0B8": "Samsung", "E0D0D1": "Samsung", "E4D3C5": "Samsung",
    "E89E8C": "Samsung", "EC7C1C": "Samsung", "F07959": "Samsung", "F0EE9C": "Samsung",
    "F42012": "Samsung", "F4401C": "Samsung", "F46D04": "Samsung", "F47B5E": "Samsung",
    "F49951": "Samsung", "F4F1E1": "Samsung", "F80332": "Samsung", "F80F41": "Samsung",
    "F87A3B": "Samsung", "F8E7D6": "Samsung", "F8F606": "Samsung", "FCAF6A": "Samsung",
    "00016B": "Huawei", "0001F4": "Huawei", "0002A8": "Huawei", "002128": "Huawei",
    "00E0FC": "Huawei", "0815A6": "Huawei", "0820A5": "Huawei", "0C37DC": "Huawei",
    "101DC3": "Huawei", "142B0B": "Huawei", "1802A2": "Huawei", "1C1D67": "Huawei",
    "00000D": "Dell", "00001A": "Dell", "0000F8": "Dell", "0010D9": "Dell",
    "0011D3": "Dell", "001372": "Dell", "00144A": "Dell", "001721": "Dell",
    "00E0DB": "Dell", "080027": "Oracle/VM", "525400": "VMware",
    "000625": "TP-Link", "001A70": "TP-Link", "001D0F": "TP-Link", "002192": "TP-Link",
    "14CC20": "TP-Link", "403F8C": "TP-Link", "50C7BF": "TP-Link", "6C3B6B": "TP-Link",
    "B0487A": "TP-Link", "C025A2": "TP-Link", "E848C6": "TP-Link", "F81A67": "TP-Link",
    "080026": "Nokia", "0001FA": "Nokia", "080028": "Nokia", "080029": "Nokia",
    "00000A": "Xerox", "00000B": "Xerox", "00000E": "Fujitsu", "00000F": "NEXT",
    "000011": "Hughes", "000014": "Netronix", "000018": "Xerox",
    "000068": "Intel", "000069": "Intel", "0000AA": "Intel", "0000E1": "Intel",
    "000E0C": "Intel", "001500": "Intel", "001D7E": "Intel", "002269": "Intel",
    "0008A1": "Microsoft", "00125A": "Microsoft", "00155D": "Microsoft",
    "001DD8": "Microsoft", "002248": "Microsoft", "2816A8": "Microsoft",
    "58408B": "Microsoft", "6045BD": "Microsoft", "7C1E52": "Microsoft",
    "00005E": "ICANN", "00005F": "Sumitomo", "000081": "Synoptics",
    "000085": "Canon", "0000A2": "Bay Networks", "0000C5": "ARIS",
    "080002": "3Com", "080009": "HP", "08001A": "Data General",
    "08001B": "Data General", "08001E": "Apollo", "080020": "Sun",
}


def get_network_info():
    """Get local network IP, subnet mask, and gateway."""
    try:
        out = subprocess.check_output("ipconfig", shell=True, timeout=5).decode(errors="ignore")
        ip, mask, gateway = None, None, None
        for line in out.splitlines():
            if "IPv4" in line or "IP Address" in line:
                m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if m: ip = m.group(1)
            if "Subnet Mask" in line:
                m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if m: mask = m.group(1)
            if "Default Gateway" in line:
                m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if m and m.group(1) != "0.0.0.0": gateway = m.group(1)
        return ip, mask, gateway
    except:
        return None, None, None


def arp_scan(network_cidr):
    """Use ARP to find all devices on the network."""
    devices = []
    try:
        out = subprocess.check_output(f"arp -a", shell=True, timeout=10).decode(errors="ignore")
        for line in out.splitlines():
            line = line.strip()
            # Match: IP (192.168.1.1) at mac-address [type]
            m = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})', line)
            if m:
                ip = m.group(1)
                mac = m.group(2).replace("-", ":").upper()
                vendor = get_mac_vendor(mac)
                devices.append({"ip": ip, "mac": mac, "vendor": vendor, "hostname": "", "type": classify_device(vendor, mac)})
    except:
        pass

    # Try to get hostnames
    for d in devices:
        try:
            hostname = socket.gethostbyaddr(d["ip"])[0]
            d["hostname"] = hostname
        except:
            pass

    return devices


def get_mac_vendor(mac):
    """Look up MAC vendor from built-in database."""
    clean = mac.replace(":", "").replace("-", "").upper()[:6]
    return MAC_VENDORS.get(clean, "Unknown")


def classify_device(vendor, mac):
    """Classify device type based on vendor and MAC."""
    vendor_lower = vendor.lower()
    if any(x in vendor_lower for x in ["apple"]):
        return "📱 Mobile/Apple"
    if any(x in vendor_lower for x in ["samsung", "xiaomi", "huawei", "nokia"]):
        return "📱 Mobile"
    if any(x in vendor_lower for x in ["cisco", "tp-link", "netgear", "d-link", "linksys", "asus"]):
        return "🌐 Router"
    if any(x in vendor_lower for x in ["intel", "dell", "hp", "lenovo", "asus", "microsoft"]):
        return "💻 PC/Laptop"
    if any(x in vendor_lower for x in ["vmware", "oracle"]):
        return "🖥️ Virtual"
    if any(x in vendor_lower for x in ["canon", "xerox", "brother"]):
        return "🖨️ Printer"
    return "❓ Unknown"


def ping_sweep(network_base):
    """Quick ping sweep to discover active hosts."""
    active = []
    base = ".".join(network_base.split(".")[:3])
    threads_list = []

    def _ping(host):
        try:
            r = subprocess.run(f"ping -n 1 -w 200 {host}", shell=True,
                             capture_output=True, timeout=1)
            if r.returncode == 0:
                active.append(host)
        except:
            pass

    for i in range(1, 255):
        t = threading.Thread(target=_ping, args=(f"{base}.{i}",), daemon=True)
        t.start()
        threads_list.append(t)
        if len(threads_list) >= 30:
            for t in threads_list: t.join(timeout=2)
            threads_list.clear()
    for t in threads_list: t.join(timeout=2)
    return active


def scan_ports(ip, ports=None):
    """Scan common ports on a device."""
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
                 993, 995, 1433, 1723, 3306, 3389, 5432, 5900, 6379,
                 8080, 8443, 9090, 27017]
    open_ports = []
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip, port)) == 0:
                service = {
                    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
                    80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS",
                    143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS",
                    995: "POP3S", 1433: "MSSQL", 1723: "PPTP", 3306: "MySQL",
                    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
                    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 9090: "Web",
                    27017: "MongoDB"
                }.get(port, f"Port-{port}")
                open_ports.append({"port": port, "service": service})
            s.close()
        except:
            pass
    return open_ports


class NetGuard:
    def __init__(self, root):
        self.root = root
        self.root.title("NETGUARD - WiFi Security Scanner")
        self.root.geometry("860x600")
        self.root.minsize(650, 450)
        self.root.configure(bg=C["bg"])
        self._center()
        self.devices = []
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 860) // 2
        y = (self.root.winfo_screenheight() - 600) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="📡 NETGUARD", font=("Segoe UI", 16, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="WiFi Network Security Scanner", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Network info
        ip, mask, gateway = get_network_info()
        info_f = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        info_f.pack(fill=tk.X, padx=16, pady=(8, 0), ipady=8)
        self.net_info = tk.Label(info_f, text=f"🌐 IP: {ip or '?'} | Mask: {mask or '?'} | Gateway: {gateway or '?'}",
                                 font=("Consolas", 9), fg=C["text"], bg=C["card"])
        self.net_info.pack(padx=12, anchor="w")

        # Control bar
        ctrl = tk.Frame(self.root, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=16, pady=(6, 0))
        self.scan_btn = tk.Button(ctrl, text="🔍 SCAN NETWORK", command=self._scan,
                                  font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#000",
                                  relief=tk.FLAT, padx=18, pady=5, cursor="hand2")
        self.scan_btn.pack(side=tk.LEFT)
        tk.Button(ctrl, text="📡 ARP Scan", command=self._arp_only,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="📋 Export", command=self._export,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        self.status_lbl = tk.Label(ctrl, text="Ready — Click SCAN NETWORK", font=("Segoe UI", 9),
                                   fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.RIGHT)

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="indeterminate", length=150)

        # Device tree
        tf = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))

        cols = ("ip", "mac", "vendor", "hostname", "type", "ports")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for c, w, t in [("ip", 120, "IP Address"), ("mac", 140, "MAC Address"),
                         ("vendor", 120, "Vendor"), ("hostname", 140, "Hostname"),
                         ("type", 100, "Type"), ("ports", 180, "Open Ports")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor="w")
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"],
                     rowheight=26, font=("Consolas", 8), borderwidth=0)
        st2.map("Treeview", background=[("selected", C["accent"])])
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._scan_ports_device)

        # Bottom toolbar
        tbar = tk.Frame(self.root, bg=C["bg2"], height=28)
        tbar.pack(fill=tk.X, side=tk.BOTTOM)
        tbar.pack_propagate(False)
        self.tool_status = tk.Label(tbar, text="Double-click a device to scan its ports",
                                    font=("Segoe UI", 8), fg=C["dim"], bg=C["bg2"])
        self.tool_status.pack(side=tk.LEFT, padx=12, pady=4)

    def _scan(self):
        self.devices = []
        self.tree.delete(*self.tree.get_children())
        self.scan_btn.config(text="⏳ Scanning...", state=tk.DISABLED, bg=C["bg2"], fg=C["dim"])
        self.progress.pack(side=tk.LEFT, padx=4)
        self.progress.start(8)
        self.status_lbl.config(text="Scanning network...", fg=C["blue"])

        def _run():
            ip, mask, gateway = get_network_info()
            self.root.after(0, lambda: self.net_info.config(
                text=f"🌐 IP: {ip or '?'} | Mask: {mask or '?'} | Gateway: {gateway or '?'}"))

            # ARP scan
            self.root.after(0, lambda: self.status_lbl.config(text="ARP scanning...", fg=C["blue"]))
            devices = arp_scan("")

            self.devices = devices
            self.root.after(0, self._show_devices)
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"Found {len(devices)} devices", fg=C["green"]))

        threading.Thread(target=_run, daemon=True).start()

    def _arp_only(self):
        self.devices = []
        self.tree.delete(*self.tree.get_children())

        def _run():
            devices = arp_scan("")
            self.devices = devices
            self.root.after(0, self._show_devices)
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"ARP: {len(devices)} devices", fg=C["green"]))

        threading.Thread(target=_run, daemon=True).start()

    def _show_devices(self):
        self.scan_btn.config(text="🔍 SCAN NETWORK", state=tk.NORMAL, bg=C["accent"], fg="#000")
        self.progress.stop()
        self.progress.pack_forget()
        self.tree.delete(*self.tree.get_children())
        for d in self.devices:
            self.tree.insert("", tk.END, values=(
                d["ip"], d["mac"], d["vendor"], d.get("hostname", ""),
                d.get("type", "?"), ""
            ))

    def _scan_ports_device(self, event):
        sel = self.tree.selection()
        if not sel: return
        values = self.tree.item(sel[0])["values"]
        ip = values[0]
        self.tool_status.config(text=f"Scanning ports on {ip}...", fg=C["blue"])

        def _run():
            ports = scan_ports(ip)
            ports_str = ", ".join(f"{p['port']}({p['service']})" for p in ports) if ports else "No open ports"
            self.root.after(0, lambda: self._update_ports(sel[0], ports_str))
            sev = "MEDIUM" if ports else "INFO"
            self.root.after(0, lambda: self.tool_status.config(
                text=f"{ip}: {len(ports)} open ports - {ports_str[:80]}",
                fg=C["orange"] if ports else C["green"]))

        threading.Thread(target=_run, daemon=True).start()

    def _update_ports(self, item, ports_str):
        values = list(self.tree.item(item)["values"])
        values[5] = ports_str
        self.tree.item(item, values=values)

    def _export(self):
        if not self.devices:
            messagebox.showinfo("No data", "Scan the network first.")
            return
        fp = tk.filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV", "*.csv"), ("JSON", "*.json")],
                                             initialfile="netguard_scan.csv")
        if not fp: return
        if fp.endswith(".json"):
            with open(fp, "w") as f:
                json.dump({"date": datetime.now().isoformat(), "devices": self.devices}, f, indent=2)
        else:
            import csv
            with open(fp, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["IP", "MAC", "Vendor", "Hostname", "Type"])
                for d in self.devices:
                    w.writerow([d["ip"], d["mac"], d["vendor"], d.get("hostname", ""), d.get("type", "")])
        messagebox.showinfo("Exported", f"Saved to:\n{fp}")


def main():
    root = tk.Tk()
    NetGuard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
