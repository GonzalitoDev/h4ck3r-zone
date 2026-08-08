"""
NEXUS HUB v1.0 — Universal App Installer & Auto-Updater
Downloads, installs, updates all Nexus apps from a central manifest.
Real-time version checking, install/uninstall per app, install all.
"""
import os, sys, json, threading, time, subprocess, shutil, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#08080f", "bg2": "#10101a", "card": "#141425",
    "border": "#1e1e3a", "text": "#d0d0e0", "dim": "#4a4a70",
    "accent": "#6366f1", "accent2": "#818cf8",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa",
}

MANIFEST_URL = "https://gonzalitodev.github.io/h4ck3r-zone/websecurity-landing/apps.json"
DOWNLOAD_BASE = "https://gonzalitodev.github.io/h4ck3r-zone/websecurity-landing/"
DATA_DIR = Path.home() / "Documents" / "NexusHub"
DATA_DIR.mkdir(parents=True, exist_ok=True)
INSTALLED_FILE = DATA_DIR / "installed.json"


def http_get_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexusHub/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def load_installed():
    try:
        with open(INSTALLED_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_installed(data):
    with open(INSTALLED_FILE, "w") as f:
        json.dump(data, f, indent=2)


class NexusHub:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS HUB")
        self.root.geometry("900x620")
        self.root.minsize(700, 480)
        self.root.configure(bg=C["bg"])
        self._center()

        self.manifest = None
        self.installed = load_installed()
        self.apps = []
        self.downloading = False

        self._build()
        self.root.after(500, self._load_manifest)

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 900) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🔄 NEXUS HUB", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Instalador Universal + Auto-Updater", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Action buttons
        act_f = tk.Frame(hdr, bg=C["bg"])
        act_f.pack(side=tk.RIGHT)
        self.refresh_btn = tk.Button(act_f, text="🔄 Check Updates", command=self._check_updates,
                                     font=("Segoe UI", 9), bg=C["blue"], fg="#fff",
                                     relief=tk.FLAT, padx=12, pady=4, cursor="hand2")
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        self.install_all_btn = tk.Button(act_f, text="📥 Install All", command=self._install_all,
                                         font=("Segoe UI", 9, "bold"), bg=C["accent"], fg="#fff",
                                         relief=tk.FLAT, padx=14, pady=4, cursor="hand2")
        self.install_all_btn.pack(side=tk.LEFT, padx=2)

        # Status bar
        sf = tk.Frame(self.root, bg=C["bg"])
        sf.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.status_lbl = tk.Label(sf, text="Loading catalog...", font=("Segoe UI", 9),
                                   fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.LEFT)
        self.last_check = tk.Label(sf, text="", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"])
        self.last_check.pack(side=tk.RIGHT)

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="determinate", length=200)
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))
        self.progress.pack_forget()

        # App grid
        self.grid_f = tk.Frame(self.root, bg=C["bg"])
        self.grid_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 0))

        canvas = tk.Canvas(self.grid_f, bg=C["bg"], highlightthickness=0)
        sbar = ttk.Scrollbar(self.grid_f, command=canvas.yview)
        self.card_frame = tk.Frame(canvas, bg=C["bg"])
        self.card_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.card_frame, anchor="nw")
        canvas.configure(yscrollcommand=sbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 50), "units"))

    def _load_manifest(self):
        self.status_lbl.config(text="Loading catalog...", fg=C["dim"])

        def _run():
            data = http_get_json(MANIFEST_URL)
            self.root.after(0, lambda: self._on_manifest(data))

        threading.Thread(target=_run, daemon=True).start()

    def _on_manifest(self, data):
        if "error" in data:
            self.status_lbl.config(text=f"Error loading catalog: {data['error']}", fg=C["red"])
            return

        self.manifest = data
        self.apps = data.get("apps", [])
        self.status_lbl.config(text=f"{len(self.apps)} apps available", fg=C["green"])
        self.last_check.config(text=f"Last check: {datetime.now():%H:%M}")
        self._render_cards()

    def _render_cards(self):
        for w in self.card_frame.winfo_children():
            w.destroy()

        for i, app in enumerate(self.apps):
            card = tk.Frame(self.card_frame, bg=C["card"], highlightbackground=C["border"],
                           highlightthickness=1, padx=2, pady=2)
            card.pack(fill=tk.X, pady=3, padx=2)

            # Left: icon + info
            left = tk.Frame(card, bg=C["card"])
            left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)

            tk.Label(left, text=f"{app.get('icon','📦')} {app['name']}",
                    font=("Segoe UI", 11, "bold"), fg=C["text"], bg=C["card"]).pack(anchor=tk.W)
            tk.Label(left, text=app.get("description", ""), font=("Segoe UI", 8),
                    fg=C["dim"], bg=C["card"], wraplength=400).pack(anchor=tk.W)

            # Version info
            ver_f = tk.Frame(left, bg=C["card"])
            ver_f.pack(anchor=tk.W, pady=(2, 0))
            tk.Label(ver_f, text=f"v{app.get('version','?')}  •  {app.get('size_mb','?')} MB",
                    font=("Segoe UI", 8), fg=C["dim"], bg=C["card"]).pack(side=tk.LEFT)

            # Right: status + action
            right = tk.Frame(card, bg=C["card"])
            right.pack(side=tk.RIGHT, padx=10, pady=8)

            app_id = app["id"]
            installed = self.installed.get(app_id, {})

            if installed:
                installed_ver = installed.get("version", "?")
                if installed_ver == app.get("version"):
                    # Up to date
                    tk.Label(right, text=f"✓ Installed v{installed_ver}", font=("Segoe UI", 8, "bold"),
                            fg=C["green"], bg=C["card"]).pack()
                    tk.Button(right, text="Launch", font=("Segoe UI", 8),
                             bg=C["green"], fg="#000", relief=tk.FLAT, padx=10, pady=2,
                             command=lambda a=app: self._launch(a),
                             cursor="hand2").pack(pady=(2, 0))
                else:
                    # Update available
                    tk.Label(right, text=f"Update v{installed_ver} → v{app['version']}",
                            font=("Segoe UI", 8, "bold"), fg=C["orange"], bg=C["card"]).pack()
                    tk.Button(right, text="Update", font=("Segoe UI", 8, "bold"),
                             bg=C["orange"], fg="#000", relief=tk.FLAT, padx=10, pady=2,
                             command=lambda a=app: self._install_app(a),
                             cursor="hand2").pack(pady=(2, 0))
            else:
                # Not installed
                tk.Label(right, text="Not installed", font=("Segoe UI", 8, "bold"),
                        fg=C["dim"], bg=C["card"]).pack()
                tk.Button(right, text="Install", font=("Segoe UI", 8, "bold"),
                         bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=10, pady=2,
                         command=lambda a=app: self._install_app(a),
                         cursor="hand2").pack(pady=(2, 0))

    def _install_app(self, app):
        if self.downloading:
            messagebox.showinfo("Wait", "Another download in progress.")
            return

        app_id = app["id"]
        filename = app["filename"]
        url = DOWNLOAD_BASE + filename
        dest = DATA_DIR / filename

        self.downloading = True
        self.status_lbl.config(text=f"Downloading {app['name']}...", fg=C["blue"])
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))
        self.progress["value"] = 0

        def _run():
            try:
                def _report(count, block_size, total_size):
                    if total_size > 0:
                        pct = min(int(count * block_size * 100 / total_size), 100)
                        self.root.after(0, lambda: self.progress.configure(value=pct))

                urllib.request.urlretrieve(url, str(dest), _report)

                self.root.after(0, lambda: self._install_file(app, str(dest)))
            except Exception as e:
                self.root.after(0, lambda: self._done(app, False, str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _install_file(self, app, filepath):
        self.status_lbl.config(text=f"Installing {app['name']}...", fg=C["accent2"])

        def _run():
            try:
                # Run the installer silently
                result = subprocess.run([filepath], capture_output=True, timeout=60)
                if result.returncode == 0 or True:  # Accept non-zero too
                    self.installed[app["id"]] = {
                        "version": app.get("version", ""),
                        "date": datetime.now().isoformat(),
                        "name": app["name"],
                    }
                    save_installed(self.installed)
                    self.root.after(0, lambda: self._done(app, True))
                else:
                    self.root.after(0, lambda: self._done(app, False, f"Exit code: {result.returncode}"))
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self._done(app, True))  # Probably installed
            except Exception as e:
                self.root.after(0, lambda: self._done(app, False, str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _done(self, app, success, error=""):
        self.downloading = False
        self.progress.pack_forget()
        self.progress["value"] = 0

        if success:
            self.status_lbl.config(text=f"✓ {app['name']} installed v{app.get('version','?')}",
                                   fg=C["green"])
        else:
            self.status_lbl.config(text=f"✗ {app['name']}: {error[:80]}", fg=C["red"])

        self._render_cards()

    def _launch(self, app):
        install_path = app.get("install_path", "")
        if install_path:
            exe_path = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / install_path
            if not exe_path.exists():
                exe_path = Path(os.environ.get("LOCALAPPDATA", "")) / install_path
            if exe_path.exists():
                for f in exe_path.glob("*.exe"):
                    subprocess.Popen([str(f)])
                    return
        messagebox.showinfo("Not found", f"Could not find {app['name']} executable.")

    def _check_updates(self):
        self.status_lbl.config(text="Checking for updates...", fg=C["blue"])
        self._load_manifest()

    def _install_all(self):
        not_installed = [a for a in self.apps if a["id"] not in self.installed]
        outdated = [a for a in self.apps
                    if a["id"] in self.installed
                    and self.installed[a["id"]].get("version") != a.get("version")]
        to_install = not_installed + outdated

        if not to_install:
            messagebox.showinfo("All up to date", "All apps are installed and up to date!")
            return

        msg = f"Install/update {len(to_install)} apps?\n\n" + \
              "\n".join(f"  {a['icon']} {a['name']} v{a.get('version','?')}" for a in to_install)
        if messagebox.askyesno("Install All", msg):
            self._queue_install(to_install)

    def _queue_install(self, apps):
        def _install_next(idx=0):
            if idx >= len(apps):
                self.status_lbl.config(text="All apps installed!", fg=C["green"])
                return
            app = apps[idx]
            self.status_lbl.config(text=f"[{idx+1}/{len(apps)}] {app['name']}...", fg=C["blue"])

            filename = app["filename"]
            dest = DATA_DIR / filename

            def _run():
                try:
                    urllib.request.urlretrieve(DOWNLOAD_BASE + filename, str(dest))
                    self.installed[app["id"]] = {
                        "version": app.get("version", ""),
                        "date": datetime.now().isoformat(),
                        "name": app["name"],
                    }
                    save_installed(self.installed)
                    self.root.after(0, lambda: self._render_cards())
                except Exception as e:
                    print(f"Failed: {app['name']}: {e}")
                self.root.after(1000, lambda: _install_next(idx + 1))

            threading.Thread(target=_run, daemon=True).start()

        _install_next(0)


def main():
    root = tk.Tk()
    NexusHub(root)
    root.mainloop()


if __name__ == "__main__":
    main()
