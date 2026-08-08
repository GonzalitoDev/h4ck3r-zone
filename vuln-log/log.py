"""
VULNLOG v1.0 — Web Vulnerability Registry & Log Manager
SQLite database for storing, searching, and managing vulnerability findings.
Add/edit/delete, filter by severity/URL, import/export, remediation tracking.
"""
import os, sys, json, sqlite3, threading, csv, re
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog

C = {
    "bg": "#0a080c", "bg2": "#14101a", "card": "#1a1426",
    "border": "#2a1e40", "text": "#d8d0e8", "dim": "#584870",
    "accent": "#a855f7", "accent2": "#c084fc",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa",
    "critical": "#f87171", "high": "#fb923c", "medium": "#fbbf24",
    "low": "#60a5fa", "info": "#584870",
}

DATA_DIR = Path.home() / "Documents" / "VulnLog"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "vulnerabilities.db"

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
STATUS_ORDER = {"OPEN": 0, "IN PROGRESS": 1, "FIXED": 2, "FALSE POSITIVE": 3}

VULN_TYPES = [
    "SQL Injection", "XSS", "CSRF", "CORS", "Security Headers",
    "TLS/SSL", "Information Disclosure", "Open Redirect", "LFI/RFI",
    "Command Injection", "Authentication", "Authorization",
    "Cookie Security", "DNS", "Port Exposure", "Subdomain Takeover",
    "Deprecated Software", "Default Credentials", "File Upload",
    "Server Misconfiguration", "Other"
]


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS vulnerabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        type TEXT DEFAULT 'Other',
        severity TEXT DEFAULT 'MEDIUM',
        status TEXT DEFAULT 'OPEN',
        description TEXT DEFAULT '',
        evidence TEXT DEFAULT '',
        recommendation TEXT DEFAULT '',
        cve_id TEXT DEFAULT '',
        cvss_score REAL DEFAULT 0,
        found_date TEXT NOT NULL,
        fixed_date TEXT DEFAULT '',
        notes TEXT DEFAULT ''
    )""")
    conn.commit()
    return conn


class VulnLog:
    def __init__(self, root):
        self.root = root
        self.root.title("VULNLOG - Web Vulnerability Registry")
        self.root.geometry("1000x640")
        self.root.minsize(750, 480)
        self.root.configure(bg=C["bg"])
        self._center()

        self.conn = init_db()
        self._build()
        self._refresh()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1000) // 2
        y = (self.root.winfo_screenheight() - 640) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="📋 VULNLOG", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Web Vulnerability Registry", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Stats bar
        sf = tk.Frame(hdr, bg=C["bg"])
        sf.pack(side=tk.RIGHT)
        self.stat_total = tk.Label(sf, text="Total: 0", font=("Segoe UI", 9, "bold"),
                                   fg=C["text"], bg=C["bg"])
        self.stat_total.pack(side=tk.LEFT, padx=8)
        self.stat_open = tk.Label(sf, text="Open: 0", font=("Segoe UI", 9, "bold"),
                                  fg=C["red"], bg=C["bg"])
        self.stat_open.pack(side=tk.LEFT, padx=8)
        self.stat_fixed = tk.Label(sf, text="Fixed: 0", font=("Segoe UI", 9, "bold"),
                                   fg=C["green"], bg=C["bg"])
        self.stat_fixed.pack(side=tk.LEFT, padx=8)

        # Toolbar
        tbar = tk.Frame(self.root, bg=C["bg"])
        tbar.pack(fill=tk.X, padx=16, pady=(6, 0))
        tk.Button(tbar, text="＋ Add", command=self._add_vuln,
                 font=("Segoe UI", 9, "bold"), bg=C["accent"], fg="#fff",
                 relief=tk.FLAT, padx=14, pady=4, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(tbar, text="✎ Edit", command=self._edit_vuln,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=3)
        tk.Button(tbar, text="🗑 Delete", command=self._delete_vuln,
                 font=("Segoe UI", 9), bg=C["red"], fg="#fff", relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=3)
        tk.Button(tbar, text="✓ Mark Fixed", command=lambda: self._change_status("FIXED"),
                 font=("Segoe UI", 9), bg=C["green"], fg="#000", relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=3)

        # Search
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh())
        search_e = tk.Entry(tbar, textvariable=self.search_var, font=("Segoe UI", 9),
                           bg=C["bg2"], fg=C["text"], insertbackground=C["accent"],
                           relief=tk.FLAT, width=20)
        search_e.pack(side=tk.RIGHT, ipady=3)
        search_e.insert(0, "")
        tk.Label(tbar, text="🔍", font=("Segoe UI", 10), fg=C["dim"], bg=C["bg"]).pack(side=tk.RIGHT)

        # Import/Export
        tk.Button(tbar, text="📥 Import", command=self._import,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT, padx=3)
        tk.Button(tbar, text="📤 Export", command=self._export,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT, padx=3)

        # Filter bar
        flt = tk.Frame(self.root, bg=C["bg"])
        flt.pack(fill=tk.X, padx=16, pady=(4, 0))
        tk.Label(flt, text="Filter:", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT)
        self.filter_sev = tk.StringVar(value="All")
        ttk.Combobox(flt, textvariable=self.filter_sev, values=["All","CRITICAL","HIGH","MEDIUM","LOW","INFO"],
                    state="readonly", font=("Segoe UI", 8), width=10).pack(side=tk.LEFT, padx=4)
        self.filter_sev.trace_add("write", lambda *a: self._refresh())
        self.filter_status = tk.StringVar(value="All")
        ttk.Combobox(flt, textvariable=self.filter_status, values=["All","OPEN","IN PROGRESS","FIXED","FALSE POSITIVE"],
                    state="readonly", font=("Segoe UI", 8), width=14).pack(side=tk.LEFT, padx=4)
        self.filter_status.trace_add("write", lambda *a: self._refresh())

        # Main tree
        tf = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))
        cols = ("id","sev","status","type","title","url","cve","date")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for c, w, t in [("id",30,"#"),("sev",60,"Severity"),("status",80,"Status"),
                         ("type",120,"Type"),("title",220,"Title"),("url",250,"URL"),
                         ("cve",100,"CVE"),("date",100,"Date")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor="w")
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"],
                     rowheight=26, font=("Segoe UI", 8), borderwidth=0)
        st2.map("Treeview", background=[("selected", C["accent"])])
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._view_detail)

        # Detail panel
        det = tk.Frame(self.root, bg=C["bg2"], height=80)
        det.pack(fill=tk.X, side=tk.BOTTOM, padx=16, pady=(0, 6))
        det.pack_propagate(False)
        self.detail_text = scrolledtext.ScrolledText(det, bg=C["bg"], fg=C["text"],
                                                      font=("Consolas", 8), wrap=tk.WORD,
                                                      relief=tk.FLAT, borderwidth=0, height=5)
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        query = "SELECT * FROM vulnerabilities WHERE 1=1"
        params = []

        if self.search_var.get():
            q = self.search_var.get()
            query += " AND (title LIKE ? OR url LIKE ? OR type LIKE ? OR cve_id LIKE ?)"
            params.extend([f"%{q}%"] * 4)

        if self.filter_sev.get() != "All":
            query += " AND severity = ?"
            params.append(self.filter_sev.get())

        if self.filter_status.get() != "All":
            query += " AND status = ?"
            params.append(self.filter_status.get())

        query += " ORDER BY id DESC LIMIT 200"

        rows = self.conn.execute(query, params).fetchall()
        for r in rows:
            sev = r[4]
            status = r[5]
            self.tree.insert("", tk.END, values=(
                r[0], sev, status, r[3], r[1], r[2][:50], r[9], r[10][:10]
            ), tags=(sev, status))

        for s in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]:
            self.tree.tag_configure(s, foreground={"CRITICAL":C["critical"],"HIGH":C["high"],
                "MEDIUM":C["medium"],"LOW":C["low"],"INFO":C["info"]}[s])
        for s in ["OPEN","IN PROGRESS","FIXED","FALSE POSITIVE"]:
            self.tree.tag_configure(s, background={"OPEN":"#2a1010","IN PROGRESS":"#2a2010",
                "FIXED":"#102a10","FALSE POSITIVE":"#10102a"}[s])

        # Update stats
        total = self.conn.execute("SELECT COUNT(*) FROM vulnerabilities").fetchone()[0]
        open_count = self.conn.execute("SELECT COUNT(*) FROM vulnerabilities WHERE status='OPEN'").fetchone()[0]
        fixed = self.conn.execute("SELECT COUNT(*) FROM vulnerabilities WHERE status='FIXED'").fetchone()[0]
        self.stat_total.config(text=f"Total: {total}")
        self.stat_open.config(text=f"Open: {open_count}")
        self.stat_fixed.config(text=f"Fixed: {fixed}")

    def _add_vuln(self):
        win = tk.Toplevel(self.root)
        win.title("Add Vulnerability"); win.geometry("550x520")
        win.configure(bg=C["bg"]); win.transient(self.root); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 550) // 2; y = (win.winfo_screenheight() - 520) // 2
        win.geometry(f"+{x}+{y}")

        fields = [
            ("Title *", "title", tk.Entry),
            ("URL *", "url", tk.Entry),
            ("Type", "type", ttk.Combobox),
            ("Severity", "severity", ttk.Combobox),
            ("Description", "description", scrolledtext.ScrolledText),
            ("Evidence", "evidence", scrolledtext.ScrolledText),
            ("Recommendation", "recommendation", scrolledtext.ScrolledText),
            ("CVE ID", "cve_id", tk.Entry),
            ("CVSS Score", "cvss_score", tk.Entry),
        ]
        entries = {}
        for label, key, wtype in fields:
            f = tk.Frame(win, bg=C["bg"]); f.pack(fill=tk.X, padx=20, pady=2)
            tk.Label(f, text=label, font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"],
                    width=12, anchor="w").pack(side=tk.LEFT)
            if wtype == scrolledtext.ScrolledText:
                w = wtype(f, height=2, bg=C["bg2"], fg=C["text"], font=("Consolas", 9),
                         wrap=tk.WORD, relief=tk.FLAT, borderwidth=0)
                w.pack(side=tk.LEFT, fill=tk.X, expand=True)
            elif wtype == ttk.Combobox:
                if key == "type":
                    w = wtype(f, values=VULN_TYPES, state="readonly", font=("Segoe UI", 9))
                    w.set("Other")
                else:
                    w = wtype(f, values=["CRITICAL","HIGH","MEDIUM","LOW","INFO"],
                            state="readonly", font=("Segoe UI", 9))
                    w.set("MEDIUM")
                w.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                w = wtype(f, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                         insertbackground=C["accent"], relief=tk.FLAT)
                w.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
            entries[key] = w

        def _save():
            title = entries["title"].get().strip()
            url = entries["url"].get().strip()
            if not title or not url:
                messagebox.showwarning("Required", "Title and URL are required."); return
            self.conn.execute("""INSERT INTO vulnerabilities
                (title,url,type,severity,status,description,evidence,recommendation,cve_id,cvss_score,found_date)
                VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
                (title, url,
                 entries["type"].get() if isinstance(entries["type"], ttk.Combobox) else "Other",
                 entries["severity"].get() if isinstance(entries["severity"], ttk.Combobox) else "MEDIUM",
                 "OPEN",
                 entries["description"].get(1.0, tk.END).strip() if isinstance(entries["description"], scrolledtext.ScrolledText) else "",
                 entries["evidence"].get(1.0, tk.END).strip() if isinstance(entries["evidence"], scrolledtext.ScrolledText) else "",
                 entries["recommendation"].get(1.0, tk.END).strip() if isinstance(entries["recommendation"], scrolledtext.ScrolledText) else "",
                 entries["cve_id"].get().strip(),
                 entries["cvss_score"].get().strip() or "0"))
            self.conn.commit()
            self._refresh()
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=6,
                 cursor="hand2").pack(pady=(10, 0))

    def _edit_vuln(self):
        sel = self.tree.selection()
        if not sel: return
        vid = self.tree.item(sel[0])["values"][0]
        row = self.conn.execute("SELECT * FROM vulnerabilities WHERE id=?", (vid,)).fetchone()
        if not row: return

        win = tk.Toplevel(self.root)
        win.title("Edit Vulnerability"); win.geometry("550x520")
        win.configure(bg=C["bg"]); win.transient(self.root); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 550) // 2; y = (win.winfo_screenheight() - 520) // 2
        win.geometry(f"+{x}+{y}")

        entries = {}
        fields_data = [
            ("Title *", "title", tk.Entry, row[1]),
            ("URL *", "url", tk.Entry, row[2]),
            ("Type", "type", ttk.Combobox, row[3]),
            ("Severity", "severity", ttk.Combobox, row[4]),
            ("Status", "status", ttk.Combobox, row[5]),
            ("CVE ID", "cve_id", tk.Entry, row[9] or ""),
            ("CVSS Score", "cvss_score", tk.Entry, str(row[11] if row[11] else "")),
        ]
        for label, key, wtype, default in fields_data:
            f = tk.Frame(win, bg=C["bg"]); f.pack(fill=tk.X, padx=20, pady=2)
            tk.Label(f, text=label, font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"],
                    width=12, anchor="w").pack(side=tk.LEFT)
            if wtype == ttk.Combobox:
                if key == "type":
                    w = wtype(f, values=VULN_TYPES, state="readonly", font=("Segoe UI", 9))
                elif key == "severity":
                    w = wtype(f, values=["CRITICAL","HIGH","MEDIUM","LOW","INFO"], state="readonly", font=("Segoe UI", 9))
                else:
                    w = wtype(f, values=["OPEN","IN PROGRESS","FIXED","FALSE POSITIVE"], state="readonly", font=("Segoe UI", 9))
                w.set(str(default))
                w.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                w = wtype(f, font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"],
                         insertbackground=C["accent"], relief=tk.FLAT)
                w.insert(0, str(default))
                w.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
            entries[key] = w

        def _save():
            self.conn.execute("""UPDATE vulnerabilities SET title=?,url=?,type=?,severity=?,status=?,
                cve_id=?,cvss_score=? WHERE id=?""",
                (entries["title"].get().strip(), entries["url"].get().strip(),
                 entries["type"].get(), entries["severity"].get(),
                 entries["status"].get(), entries["cve_id"].get().strip(),
                 entries["cvss_score"].get().strip() or "0", vid))
            self.conn.commit()
            self._refresh()
            win.destroy()

        tk.Button(win, text="SAVE", command=_save, font=("Segoe UI", 10, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=20, pady=6,
                 cursor="hand2").pack(pady=(10, 0))

    def _delete_vuln(self):
        sel = self.tree.selection()
        if not sel: return
        vid = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Delete", f"Delete vulnerability #{vid}?"):
            self.conn.execute("DELETE FROM vulnerabilities WHERE id=?", (vid,))
            self.conn.commit()
            self._refresh()

    def _change_status(self, new_status):
        sel = self.tree.selection()
        if not sel: return
        vid = self.tree.item(sel[0])["values"][0]
        self.conn.execute("UPDATE vulnerabilities SET status=? WHERE id=?", (new_status, vid))
        self.conn.commit()
        self._refresh()

    def _view_detail(self, event):
        sel = self.tree.selection()
        if not sel: return
        vid = self.tree.item(sel[0])["values"][0]
        row = self.conn.execute("SELECT * FROM vulnerabilities WHERE id=?", (vid,)).fetchone()
        if not row: return
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END,
            f"[{row[4]}] {row[1]}\n"
            f"URL: {row[2]}\n"
            f"Type: {row[3]} | Status: {row[5]} | CVE: {row[9]} | CVSS: {row[11]}\n"
            f"Found: {row[10]} | Fixed: {row[12] or '—'}\n"
            f"{'─'*50}\n"
            f"Description:\n{row[6] or '—'}\n\n"
            f"Evidence:\n{row[7] or '—'}\n\n"
            f"Recommendation:\n{row[8] or '—'}"
        )

    def _import(self):
        fp = filedialog.askopenfilename(filetypes=[("JSON/CSV", "*.json;*.csv")])
        if not fp: return
        count = 0
        try:
            if fp.endswith(".json"):
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                findings = data if isinstance(data, list) else data.get("findings", []) or data.get("results", [])
                for item in findings:
                    if isinstance(item, dict):
                        self.conn.execute("""INSERT INTO vulnerabilities (title,url,type,severity,status,description,evidence,recommendation,cve_id,found_date)
                            VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))""",
                            (item.get("name", item.get("title","?")),
                             item.get("url",""),
                             item.get("category", item.get("type","Other")),
                             item.get("severity","MEDIUM"),
                             "OPEN",
                             item.get("description",""),
                             item.get("evidence",""),
                             item.get("recommendation", item.get("fix","")),
                             item.get("cve_id","")))
                        count += 1
            elif fp.endswith(".csv"):
                with open(fp, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.conn.execute("""INSERT INTO vulnerabilities (title,url,severity,status,description,found_date)
                            VALUES (?,?,?,?,?,datetime('now'))""",
                            (row.get("title", row.get("name","?")),
                             row.get("url",""),
                             row.get("severity","MEDIUM"),
                             "OPEN",
                             row.get("description","")))
                        count += 1
            self.conn.commit()
            self._refresh()
            messagebox.showinfo("Imported", f"{count} vulnerabilities imported.")
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")

    def _export(self):
        fp = filedialog.asksaveasfilename(defaultextension=".json",
                                          filetypes=[("JSON", "*.json"), ("CSV", "*.csv")])
        if not fp: return
        rows = self.conn.execute("SELECT * FROM vulnerabilities ORDER BY id").fetchall()

        if fp.endswith(".json"):
            data = []
            for r in rows:
                data.append({
                    "id": r[0], "title": r[1], "url": r[2], "type": r[3],
                    "severity": r[4], "status": r[5], "description": r[6],
                    "evidence": r[7], "recommendation": r[8], "cve_id": r[9],
                    "cvss_score": r[11], "found_date": r[10], "fixed_date": r[12],
                })
            with open(fp, "w", encoding="utf-8") as f:
                json.dump({"exported": datetime.now().isoformat(), "findings": data}, f, indent=2)

        elif fp.endswith(".csv"):
            with open(fp, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["ID","Title","URL","Type","Severity","Status","Description","Evidence","Recommendation","CVE","CVSS","Found"])
                for r in rows:
                    w.writerow([r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9],r[11],r[10]])

        messagebox.showinfo("Exported", f"Exported to:\n{fp}")


def main():
    root = tk.Tk()
    VulnLog(root)
    root.mainloop()


if __name__ == "__main__":
    main()
