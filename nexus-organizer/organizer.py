"""
NEXUS ORGANIZER AI v1.0 — Smart Folder Organizer
AI-powered file classification, auto-organize, duplicate detection,
smart naming, preview before apply, undo history.
"""
import os, sys, json, threading, shutil, re, hashlib, fnmatch, time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

C = {
    "bg": "#0a0a14", "bg2": "#121225", "card": "#181835",
    "border": "#202048", "text": "#d0d0e4", "dim": "#484878",
    "accent": "#a855f7", "accent2": "#c084fc",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa", "pink": "#ec4899",
}

# AI Classification categories with extensions and keywords
CATEGORIES = {
    "📄 Documentos": {
        "ext": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".csv", ".xls", ".xlsx",
                ".ppt", ".pptx", ".log", ".tex", ".pages", ".numbers", ".key"],
        "keywords": ["doc", "report", "invoice", "resume", "cv", "contract", "letter"],
    },
    "🖼️ Imágenes": {
        "ext": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff",
                ".psd", ".ai", ".raw", ".cr2", ".nef", ".heic", ".heif"],
        "keywords": ["photo", "image", "screenshot", "captura", "foto", "img"],
    },
    "🎵 Audio": {
        "ext": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".midi", ".mid"],
        "keywords": ["audio", "music", "song", "track", "podcast", "recording"],
    },
    "🎬 Video": {
        "ext": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".ts"],
        "keywords": ["video", "movie", "clip", "recording", "stream", "film"],
    },
    "📦 Archivos": {
        "ext": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".dmg", ".pkg"],
        "keywords": ["archive", "backup", "compressed"],
    },
    "💻 Código": {
        "ext": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h", ".cs", ".go",
                ".rs", ".rb", ".php", ".swift", ".kt", ".sql", ".sh", ".bat", ".ps1", ".yaml",
                ".yml", ".json", ".xml", ".toml", ".ini", ".cfg", ".env", ".dockerfile"],
        "keywords": ["code", "script", "source", "config", "build", "project"],
    },
    "⚙️ Ejecutables/Sistema": {
        "ext": [".exe", ".msi", ".dll", ".sys", ".so", ".dylib", ".apk", ".bin", ".dat", ".db"],
        "keywords": ["setup", "install", "binary", "executable", "program"],
    },
    "📊 Datos": {
        "ext": [".csv", ".json", ".xml", ".db", ".sqlite", ".sqlite3", ".parquet", ".feather"],
        "keywords": ["data", "database", "dataset", "export", "import", "report"],
    },
    "✏️ Diseño/3D": {
        "ext": [".blend", ".fbx", ".obj", ".stl", ".3ds", ".max", ".skp", ".fig", ".xd", ".sketch"],
        "keywords": ["model", "render", "design", "3d", "mesh"],
    },
    "🔖 Otros": {
        "ext": [],
        "keywords": [],
    },
}

# Sub-organizers by time
TIME_CATEGORIES = {
    "📅 Última semana": 7,
    "📅 Último mes": 30,
    "📅 Últimos 3 meses": 90,
    "📅 Último año": 365,
    "📅 Antiguos": float("inf"),
}

# Sub-organizers by size
SIZE_CATEGORIES = {
    "📊 Pequeños (<1 MB)": 1 * 1024 * 1024,
    "📊 Medianos (1-50 MB)": 50 * 1024 * 1024,
    "📊 Grandes (50-500 MB)": 500 * 1024 * 1024,
    "📊 Enormes (>500 MB)": float("inf"),
}


def classify_file(filepath):
    """AI classifier: Determine file category based on extension + name patterns."""
    name = os.path.basename(filepath).lower()
    ext = os.path.splitext(name)[1].lower()

    for category, info in CATEGORIES.items():
        if ext in info["ext"]:
            return category
        for kw in info["keywords"]:
            if kw in name:
                return category

    return "🔖 Otros"


def classify_by_date(filepath):
    """Classify by modification date."""
    try:
        mtime = os.path.getmtime(filepath)
        age_days = (time.time() - mtime) / 86400

        for label, days in TIME_CATEGORIES.items():
            if age_days <= days:
                return label
    except:
        pass
    return "📅 Antiguos"


def classify_by_size(filepath):
    """Classify by file size."""
    try:
        size = os.path.getsize(filepath)
        for label, max_size in SIZE_CATEGORIES.items():
            if size < max_size:
                return label
    except:
        pass
    return "📊 Enormes"


def detect_duplicates(folder):
    """Find duplicate files by size + first bytes hash."""
    candidates = defaultdict(list)
    for root, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(root, f)
            try:
                sz = os.path.getsize(fp)
                if sz > 0:
                    candidates[(f.lower(), sz)].append(fp)
            except:
                pass

    dupes = []
    for (name, sz), paths in candidates.items():
        if len(paths) > 1:
            # Quick content check with first 4KB hash
            hashes = {}
            for p in paths:
                try:
                    with open(p, "rb") as file:
                        h = hashlib.md5(file.read(4096)).hexdigest()
                        hashes.setdefault(h, []).append(p)
                except:
                    pass
            for h, group in hashes.items():
                if len(group) > 1:
                    dupes.append({"name": name, "size": sz, "paths": group, "count": len(group)})

    return dupes


def smart_rename_suggestion(filepath):
    """AI-powered rename suggestion based on content pattern detection."""
    name = os.path.basename(filepath)
    name_noext, ext = os.path.splitext(name)

    suggestions = []

    # Detect date patterns in filename
    date_patterns = [
        (r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})', "Date YYYY-MM-DD"),
        (r'(\d{2})[-_]?(\d{2})[-_]?(\d{4})', "Date DD-MM-YYYY"),
        (r'Screenshot[_\s]*(\d{4}[-]?\d{2}[-]?\d{2})', "Screenshot date"),
        (r'IMG[_\s]*(\d{4})(\d{2})(\d{2})', "Photo date"),
        (r'VID[_\s]*(\d{4})(\d{2})(\d{2})', "Video date"),
    ]

    for pattern, desc in date_patterns:
        m = re.search(pattern, name, re.IGNORECASE)
        if m:
            try:
                groups = [g for g in m.groups() if g]
                if len(groups) >= 3:
                    year, month, day = groups[0], groups[1], groups[2]
                    clean = re.sub(pattern, '', name, flags=re.IGNORECASE).strip("_- ")
                    if clean:
                        suggestions.append(f"{year}-{month}-{day}_{clean}{ext}")
                    else:
                        suggestions.append(f"{year}-{month}-{day}{ext}")
            except:
                pass

    # Remove redundant numbers/spaces
    simplified = re.sub(r'[_\s]+', '_', name_noext).strip("_-")
    simplified = re.sub(r'\(\d+\)', '', simplified).strip()
    simplified = re.sub(r'copy\s*of\s*', '', simplified, flags=re.IGNORECASE).strip()
    if simplified != name_noext:
        suggestions.append(f"{simplified}{ext}")

    # Add date prefix for old files
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        suggestions.append(f"{mtime:%Y-%m-%d}_{name}")
    except:
        pass

    return suggestions[:3]  # Top 3 suggestions


class NexusOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS ORGANIZER AI")
        self.root.geometry("960x640")
        self.root.minsize(700, 480)
        self.root.configure(bg=C["bg"])
        self._center()

        self.current_folder = ""
        self.files_data = []
        self.plan = []
        self.undo_stack = []

        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 960) // 2
        y = (self.root.winfo_screenheight() - 640) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🤖 NEXUS ORGANIZER AI", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="AI-Powered Folder Organizer", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Folder selector
        sel_f = tk.Frame(self.root, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        sel_f.pack(fill=tk.X, padx=16, pady=(8, 0))
        inner = tk.Frame(sel_f, bg=C["bg2"]); inner.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(inner, text="Carpeta:", font=("Segoe UI", 9, "bold"), fg=C["dim"], bg=C["bg2"]).pack(side=tk.LEFT)
        self.path_e = tk.Entry(inner, font=("Consolas", 10), bg=C["bg"], fg=C["text"],
                               insertbackground=C["accent"], relief=tk.FLAT, width=40, borderwidth=0)
        self.path_e.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True, ipady=4)
        tk.Button(inner, text="📁", command=self._browse,
                 font=("Segoe UI", 12), bg=C["accent"], fg="#fff", relief=tk.FLAT,
                 padx=10, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(inner, text="🔍 Analizar", command=self._analyze,
                 font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                 relief=tk.FLAT, padx=14, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Stats bar
        sf = tk.Frame(self.root, bg=C["bg"])
        sf.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.stat_files = tk.Label(sf, text="Archivos: 0", font=("Segoe UI", 9), fg=C["text"], bg=C["bg"])
        self.stat_files.pack(side=tk.LEFT, padx=8)
        self.stat_dup = tk.Label(sf, text="Duplicados: 0", font=("Segoe UI", 9), fg=C["orange"], bg=C["bg"])
        self.stat_dup.pack(side=tk.LEFT, padx=8)
        self.stat_cat = tk.Label(sf, text="Categorías: 0", font=("Segoe UI", 9), fg=C["blue"], bg=C["bg"])
        self.stat_cat.pack(side=tk.LEFT, padx=8)

        # Mode selector
        self.mode_var = tk.StringVar(value="type")
        for text, mode in [("Por Tipo", "type"), ("Por Fecha", "date"), ("Por Tamaño", "size"), ("Duplicados", "dupes")]:
            tk.Radiobutton(sf, text=text, variable=self.mode_var, value=mode,
                          bg=C["bg"], fg=C["dim"], selectcolor=C["bg2"],
                          activebackground=C["bg"], font=("Segoe UI", 8)).pack(side=tk.RIGHT, padx=2)

        # Action buttons
        act_f = tk.Frame(self.root, bg=C["bg"])
        act_f.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.apply_btn = tk.Button(act_f, text="✅ Aplicar Organización", command=self._apply,
                                   font=("Segoe UI", 10, "bold"), bg=C["green"], fg="#000",
                                   relief=tk.FLAT, padx=16, pady=5, state=tk.DISABLED, cursor="hand2")
        self.apply_btn.pack(side=tk.LEFT)
        tk.Button(act_f, text="↩ Deshacer", command=self._undo,
                 font=("Segoe UI", 9), bg=C["orange"], fg="#000", relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(act_f, text="🤖 Smart Rename", command=self._smart_rename_all,
                 font=("Segoe UI", 9), bg=C["accent"], fg="#fff", relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Plan tree
        tf = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))
        cols = ("icon","action","from","to")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="extended")
        for c, w, t in [("icon",30,""),("action",80,"Acción"),("from",380,"Origen"),("to",380,"Destino")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor="w")
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"],
                     rowheight=24, font=("Consolas", 8), borderwidth=0)
        st2.map("Treeview", background=[("selected", C["accent"])])
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Status
        self.status_lbl = tk.Label(self.root, text="Seleccioná una carpeta y click Analizar",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

    def _browse(self):
        p = filedialog.askdirectory(title="Seleccionar carpeta para organizar")
        if p:
            self.path_e.delete(0, tk.END); self.path_e.insert(0, p)
            self.current_folder = p

    def _analyze(self):
        folder = self.path_e.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showwarning("Carpeta", "Seleccioná una carpeta válida.")
            return
        self.current_folder = folder
        self.status_lbl.config(text="🤖 Analizando con IA...", fg=C["accent"])

        def _run():
            mode = self.mode_var.get()
            plan = self._generate_plan(folder, mode)
            self.root.after(0, lambda: self._show_plan(plan))

        threading.Thread(target=_run, daemon=True).start()

    def _generate_plan(self, folder, mode):
        """AI generates an organization plan for the folder."""
        if mode == "dupes":
            return self._dupes_plan(folder)

        plan = []
        files = []

        # Scan folder (non-recursive by default)
        try:
            for entry in os.scandir(folder):
                if entry.is_file():
                    files.append(entry.path)
        except Exception as e:
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"Error: {e}", fg=C["red"]))
            return []

        if not files:
            return []

        if mode == "type":
            plan = self._type_plan(folder, files)
        elif mode == "date":
            plan = self._date_plan(folder, files)
        elif mode == "size":
            plan = self._size_plan(folder, files)

        self.files_data = files
        return plan

    def _type_plan(self, folder, files):
        """Organize by AI-detected type category."""
        plan = []
        for fp in files:
            category = classify_file(fp)
            dest_dir = os.path.join(folder, category)
            dest = os.path.join(dest_dir, os.path.basename(fp))

            if os.path.normpath(fp) != os.path.normpath(dest):
                plan.append({
                    "action": "📁 Mover",
                    "from": fp,
                    "to": dest,
                    "reason": f"IA clasificó como {category}",
                })
        return plan

    def _date_plan(self, folder, files):
        """Organize by modification date."""
        plan = []
        for fp in files:
            category = classify_by_date(fp)
            dest_dir = os.path.join(folder, category)
            dest = os.path.join(dest_dir, os.path.basename(fp))

            if os.path.normpath(fp) != os.path.normpath(dest):
                plan.append({
                    "action": "📅 Mover",
                    "from": fp,
                    "to": dest,
                    "reason": f"Modificado hace {category.split()[-1]}",
                })
        return plan

    def _size_plan(self, folder, files):
        """Organize by file size."""
        plan = []
        for fp in files:
            category = classify_by_size(fp)
            dest_dir = os.path.join(folder, category)
            dest = os.path.join(dest_dir, os.path.basename(fp))

            if os.path.normpath(fp) != os.path.normpath(dest):
                plan.append({
                    "action": "📊 Mover",
                    "from": fp,
                    "to": dest,
                    "reason": f"Tamaño: {category}",
                })
        return plan

    def _dupes_plan(self, folder):
        """Find and suggest removing duplicates."""
        dupes = detect_duplicates(folder)
        plan = []
        for d in dupes:
            # Keep first, move others to _Duplicates folder
            keep = d["paths"][0]
            dup_dir = os.path.join(folder, "🗑️ _Duplicados")
            for dup_path in d["paths"][1:]:
                dest = os.path.join(dup_dir, os.path.basename(dup_path))
                plan.append({
                    "action": "🗑 Duplicado",
                    "from": dup_path,
                    "to": dest,
                    "reason": f"Duplicado de '{os.path.basename(keep)}' ({d['size']//1024}KB)",
                })
                # Rename to avoid conflicts
                base, ext = os.path.splitext(dest)
                counter = 1
                existing_dests = [p["to"] for p in plan]
                while dest in existing_dests:
                    dest = f"{base}_{counter}{ext}"
                    counter += 1
                plan[-1]["to"] = dest
        return plan

    def _show_plan(self, plan):
        self.plan = plan
        self.tree.delete(*self.tree.get_children())

        cats = Counter()
        dupes = 0
        for p in plan:
            self.tree.insert("", tk.END, values=(p["action"].split()[0], p["action"],
                                                  p["from"][:80], p["to"][:80]))
            if "📁" in p["action"]:
                cats[p["reason"]] += 1
            if "Duplicado" in p["action"]:
                dupes += 1

        self.stat_files.config(text=f"Archivos: {len(self.files_data) or sum(1 for p in plan)}")
        self.stat_dup.config(text=f"Duplicados: {dupes}")
        self.stat_cat.config(text=f"Categorías: {len(cats)}")

        if plan:
            self.apply_btn.config(state=tk.NORMAL)
            self.status_lbl.config(
                text=f"🤖 Plan generado: {len(plan)} acciones. Revisá y click Aplicar.",
                fg=C["green"])
        else:
            self.apply_btn.config(state=tk.DISABLED)
            self.status_lbl.config(text="✅ La carpeta ya está organizada.", fg=C["green"])

    def _apply(self):
        if not self.plan:
            return

        ok = messagebox.askyesno("Aplicar", f"¿Ejecutar {len(self.plan)} acciones?\n\n"
                                 "Se moverán archivos a subcarpetas.\n"
                                 "Podés deshacer después.")
        if not ok:
            return

        self.undo_stack = []
        done = 0
        errors = 0

        for action in self.plan:
            try:
                src = action["from"]
                dest = action["to"]
                dest_dir = os.path.dirname(dest)

                if not os.path.exists(src):
                    continue

                os.makedirs(dest_dir, exist_ok=True)

                # Handle name conflicts
                if os.path.exists(dest):
                    base, ext = os.path.splitext(dest)
                    counter = 1
                    while os.path.exists(f"{base}_{counter}{ext}"):
                        counter += 1
                    dest = f"{base}_{counter}{ext}"
                    action["actual_to"] = dest

                shutil.move(src, dest)
                self.undo_stack.append({"from": dest, "to": src})
                done += 1
            except Exception as e:
                errors += 1

        self.tree.delete(*self.tree.get_children())
        self.plan = []
        self.apply_btn.config(state=tk.DISABLED)
        self.status_lbl.config(
            text=f"✅ {done} archivos organizados. {errors} errores. Click ↩ Deshacer para revertir.",
            fg=C["green"])

        if self.undo_stack:
            self._rescan()

    def _undo(self):
        if not self.undo_stack:
            messagebox.showinfo("Nada", "No hay acciones para deshacer.")
            return

        count = len(self.undo_stack)
        ok = messagebox.askyesno("Deshacer", f"¿Revertir {count} movimientos?")
        if not ok:
            return

        done = 0
        for action in reversed(self.undo_stack):
            try:
                os.makedirs(os.path.dirname(action["to"]), exist_ok=True)
                shutil.move(action["from"], action["to"])
                done += 1
            except:
                pass

        self.undo_stack = []
        self.status_lbl.config(text=f"↩ {done} acciones deshechas. Clickeá Analizar de nuevo.",
                               fg=C["orange"])
        self._rescan()
        self.tree.delete(*self.tree.get_children())

    def _rescan(self):
        """Quick rescan to update UI."""
        if self.current_folder:
            pass  # stats will update on next analyze

    def _smart_rename_all(self):
        """AI suggests smart renames for all files."""
        folder = self.current_folder
        if not folder:
            return

        plan = []
        try:
            for entry in os.scandir(folder):
                if entry.is_file():
                    suggestions = smart_rename_suggestion(entry.path)
                    if suggestions:
                        new_name = suggestions[0]
                        dest = os.path.join(folder, new_name)
                        if os.path.normpath(entry.path) != os.path.normpath(dest):
                            plan.append({
                                "action": "✏️ Renombrar",
                                "from": entry.path,
                                "to": dest,
                                "reason": f"IA sugiere: {new_name[:40]}",
                            })
        except:
            pass

        self._show_plan(plan)


def main():
    root = tk.Tk()
    NexusOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
