"""
NEXUS BROWSER v2.0 — Custom Web Browser .exe
Tabs, bookmarks, history, navigation. Opens pages in Edge app mode
(clean window, no browser chrome) for embedded feel.
"""
import os, sys, json, subprocess, webbrowser, urllib.parse
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

C = {
    "bg": "#0d0d15", "bg2": "#161625", "bg3": "#0a0a12",
    "border": "#1e1e38", "text": "#d0d0e0", "dim": "#484878",
    "accent": "#6366f1", "accent2": "#818cf8",
    "green": "#34d399", "red": "#f87171", "tab_active": "#1a1a30",
    "tab_inactive": "#0d0d18",
}

DATA_DIR = Path.home() / "Documents" / "NexusBrowser"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
HISTORY_FILE = DATA_DIR / "history.json"
HOME_PAGE = "https://gonzalitodev.github.io/h4ck3r-zone/websecurity-landing/"

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default or []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class Tab:
    def __init__(self, browser, title="New Tab", url=""):
        self.browser = browser
        self.title = title
        self.url = url or HOME_PAGE
        self.can_go_back = False
        self.can_go_forward = False


class NexusBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Nexus Browser")
        self.root.geometry("1100x700")
        self.root.minsize(700, 450)
        self.root.configure(bg=C["bg"])

        self.bookmarks = load_json(BOOKMARKS_FILE)
        self.history = load_json(HISTORY_FILE)
        self.tabs = []
        self.current_tab = None
        self.webview_windows = {}

        self._build()
        self._new_tab(HOME_PAGE)

        self.root.bind("<Control-t>", lambda e: self._new_tab())
        self.root.bind("<Control-w>", lambda e: self._close_tab())
        self.root.bind("<Control-l>", lambda e: self._focus_url())
        self.root.bind("<Control-d>", lambda e: self._add_bookmark())
        self.root.bind("<Control-h>", lambda e: self._show_history())
        self.root.bind("<Control-b>", lambda e: self._show_bookmarks())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        # Tab bar
        self.tab_frame = tk.Frame(self.root, bg=C["bg"], height=36)
        self.tab_frame.pack(fill=tk.X)
        self.tab_frame.pack_propagate(False)
        self.tabs_container = tk.Frame(self.tab_frame, bg=C["bg"])
        self.tabs_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(self.tab_frame, text="＋", command=lambda: self._new_tab(),
                 font=("Segoe UI", 12), bg=C["bg"], fg=C["dim"], relief=tk.FLAT,
                 bd=0, padx=8, cursor="hand2", activebackground=C["bg2"]).pack(side=tk.RIGHT)

        # Navigation bar
        nav = tk.Frame(self.root, bg=C["bg2"], height=42)
        nav.pack(fill=tk.X)
        nav.pack_propagate(False)

        # Navigation buttons
        btn_f = tk.Frame(nav, bg=C["bg2"]); btn_f.pack(side=tk.LEFT, padx=4)
        for text, cmd, tip in [("◀", self._go_back, "Back"), ("▶", self._go_forward, "Forward"),
                                ("🔄", self._refresh, "Refresh"), ("🏠", self._go_home, "Home")]:
            tk.Button(btn_f, text=text, command=cmd, font=("Segoe UI", 11),
                     bg=C["bg2"], fg=C["text"], relief=tk.FLAT, bd=0, padx=6,
                     cursor="hand2", activebackground=C["bg"]).pack(side=tk.LEFT)

        # URL bar
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(nav, textvariable=self.url_var,
                                  font=("Segoe UI", 11), bg=C["bg3"], fg=C["text"],
                                  insertbackground=C["accent"], relief=tk.FLAT, bd=0)
        self.url_entry.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True, ipady=4)
        self.url_entry.bind("<Return>", lambda e: self._navigate())

        # Action buttons
        for text, cmd in [("⭐", self._add_bookmark), ("📋", self._show_history),
                           ("⚙️", self._show_menu)]:
            tk.Button(nav, text=text, command=cmd, font=("Segoe UI", 11),
                     bg=C["bg2"], fg=C["dim"], relief=tk.FLAT, bd=0, padx=6,
                     cursor="hand2", activebackground=C["bg"]).pack(side=tk.RIGHT)

        # Main content area (webview container)
        self.content_frame = tk.Frame(self.root, bg=C["bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_frame = tk.Frame(self.root, bg=C["bg3"], height=22)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_frame.pack_propagate(False)
        self.status_lbl = tk.Label(self.status_frame, text="Ready",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg3"], anchor="w")
        self.status_lbl.pack(side=tk.LEFT, padx=10, pady=2)

    def _new_tab(self, url=""):
        if not HAS_WEBVIEW:
            if url:
                webbrowser.open(url)
            elif not self.tabs:
                webbrowser.open(HOME_PAGE)
            self.status_lbl.config(text="WebView2 not available. Install: pip install pywebview")
            return

        tab = Tab(self, url=url)
        self.tabs.append(tab)
        self._select_tab(tab)
        self._render_tabs()

    def _select_tab(self, tab):
        self.current_tab = tab
        self.url_var.set(tab.url)
        self._render_tabs()

        if not tab.url:
            return

        # Open in Edge app mode (clean window, looks like embedded browser)
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "msedge", f"--app={tab.url}",
                 "--window-size=1100,650", "--new-window"],
                shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.status_lbl.config(text=f"🌐 Opened: {tab.title or tab.url}")
        except:
            webbrowser.open(tab.url)
            self.status_lbl.config(text=f"🌐 Opened in default browser", fg=C["dim"])

        self._add_history(tab.url, tab.title)

    def _render_tabs(self):
        for w in self.tabs_container.winfo_children():
            w.destroy()

        for i, tab in enumerate(self.tabs):
            is_active = tab is self.current_tab
            color = C["tab_active"] if is_active else C["tab_inactive"]
            fg = C["text"] if is_active else C["dim"]

            tab_btn = tk.Frame(self.tabs_container, bg=color, cursor="hand2")
            tab_btn.pack(side=tk.LEFT)

            lbl = tk.Label(tab_btn, text=f"  {tab.title[:20] or 'New Tab'}  ",
                          font=("Segoe UI", 9), fg=fg, bg=color)
            lbl.pack(side=tk.LEFT, ipady=6)
            lbl.bind("<Button-1>", lambda e, t=tab: self._select_tab(t))

            close_btn = tk.Label(tab_btn, text="×", font=("Segoe UI", 10, "bold"),
                                fg=C["dim"] if not is_active else C["text"], bg=color,
                                cursor="hand2")
            close_btn.pack(side=tk.RIGHT, padx=(0, 4))
            close_btn.bind("<Button-1>", lambda e, t=tab: self._close_tab(t))
            close_btn.bind("<Enter>", lambda e, b=close_btn: b.config(fg=C["red"]))
            close_btn.bind("<Leave>", lambda e, b=close_btn, a=is_active:
                          b.config(fg=C["text"] if a else C["dim"]))

    def _close_tab(self, tab=None):
        if tab is None:
            tab = self.current_tab
        if len(self.tabs) <= 1 and tab is self.current_tab:
            self._new_tab()
            return

        idx = self.tabs.index(tab)
        self.tabs.remove(tab)

        if tab is self.current_tab:
            new_idx = min(idx, len(self.tabs) - 1)
            if self.tabs:
                self._select_tab(self.tabs[new_idx])

        self._render_tabs()

    def _navigate(self):
        url = self.url_var.get().strip()
        if not url:
            return

        # Add https:// if no scheme
        if not url.startswith(("http://", "https://")):
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                # Search query
                url = f"https://www.google.com/search?q={urllib.parse.quote(url)}"

        if self.current_tab:
            self.current_tab.url = url
            self.current_tab.title = url.split("/")[2] if "://" in url else url[:30]
        self._select_tab(self.current_tab)

    def _go_back(self):
        self.status_lbl.config(text="◀ Back (use browser controls in the page)")

    def _go_forward(self):
        self.status_lbl.config(text="▶ Forward (use browser controls in the page)")

    def _refresh(self):
        if self.current_tab:
            self._select_tab(self.current_tab)
        self.status_lbl.config(text="🔄 Refreshed")

    def _go_home(self):
        if self.current_tab:
            self.current_tab.url = HOME_PAGE
            self._select_tab(self.current_tab)

    def _focus_url(self):
        self.url_entry.focus()
        self.url_entry.select_range(0, tk.END)

    def _add_bookmark(self):
        if not self.current_tab:
            return
        url = self.current_tab.url
        title = self.current_tab.title or url

        # Check if already bookmarked
        for bm in self.bookmarks:
            if bm["url"] == url:
                messagebox.showinfo("Bookmark", "Already bookmarked.")
                return

        self.bookmarks.append({"title": title, "url": url, "date": datetime.now().isoformat()})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self.status_lbl.config(text=f"⭐ Bookmarked: {title}")

    def _show_bookmarks(self):
        win = tk.Toplevel(self.root)
        win.title("Bookmarks"); win.geometry("500x400")
        win.configure(bg=C["bg"]); win.transient(self.root)

        tk.Label(win, text="⭐ Bookmarks", font=("Segoe UI", 14, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(pady=(16, 10))

        if not self.bookmarks:
            tk.Label(win, text="No bookmarks yet. Press Ctrl+D to add.",
                    font=("Segoe UI", 10), fg=C["dim"], bg=C["bg"]).pack(expand=True)
        else:
            list_f = tk.Frame(win, bg=C["bg"])
            list_f.pack(fill=tk.BOTH, expand=True, padx=20)
            for bm in self.bookmarks:
                item = tk.Frame(list_f, bg=C["bg2"], highlightbackground=C["border"],
                               highlightthickness=1, cursor="hand2")
                item.pack(fill=tk.X, pady=2)
                tk.Label(item, text=bm["title"], font=("Segoe UI", 10, "bold"),
                        fg=C["text"], bg=C["bg2"]).pack(anchor="w", padx=10, pady=(8, 0))
                tk.Label(item, text=bm["url"], font=("Segoe UI", 8),
                        fg=C["dim"], bg=C["bg2"]).pack(anchor="w", padx=10, pady=(0, 8))
                item.bind("<Button-1>", lambda e, u=bm["url"]: self._open_bookmark(u, win))
                tk.Button(item, text="×", command=lambda b=bm: self._del_bookmark(b, win),
                         font=("Segoe UI", 10), bg=C["red"], fg="#fff", relief=tk.FLAT,
                         bd=0, padx=6, cursor="hand2").place(relx=0.96, rely=0.5, anchor="e")

    def _open_bookmark(self, url, win):
        self.current_tab.url = url
        self._select_tab(self.current_tab)
        win.destroy()

    def _del_bookmark(self, bm, win):
        self.bookmarks.remove(bm)
        save_json(BOOKMARKS_FILE, self.bookmarks)
        win.destroy()
        self._show_bookmarks()

    def _add_history(self, url, title):
        if not url or url == HOME_PAGE:
            return
        self.history.insert(0, {"title": title or url, "url": url,
                                "date": datetime.now().isoformat()})
        self.history = self.history[:100]
        save_json(HISTORY_FILE, self.history)

    def _show_history(self):
        win = tk.Toplevel(self.root)
        win.title("History"); win.geometry("500x400")
        win.configure(bg=C["bg"]); win.transient(self.root)

        tk.Label(win, text="📋 History", font=("Segoe UI", 14, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(pady=(16, 10))

        if not self.history:
            tk.Label(win, text="No history yet.",
                    font=("Segoe UI", 10), fg=C["dim"], bg=C["bg"]).pack(expand=True)
        else:
            list_f = tk.Frame(win, bg=C["bg"])
            list_f.pack(fill=tk.BOTH, expand=True, padx=20)
            for entry in self.history[:50]:
                item = tk.Frame(list_f, bg=C["bg2"], highlightbackground=C["border"],
                               highlightthickness=1, cursor="hand2")
                item.pack(fill=tk.X, pady=2)
                tk.Label(item, text=entry["title"], font=("Segoe UI", 10, "bold"),
                        fg=C["text"], bg=C["bg2"]).pack(anchor="w", padx=10, pady=(8, 0))
                tk.Label(item, text=entry["url"][:60], font=("Segoe UI", 8),
                        fg=C["dim"], bg=C["bg2"]).pack(anchor="w", padx=10, pady=(0, 8))
                item.bind("<Button-1>", lambda e, u=entry["url"]:
                         self._open_bookmark(u, win))
            tk.Button(win, text="Clear History", font=("Segoe UI", 9),
                     bg=C["red"], fg="#fff", relief=tk.FLAT, padx=12, pady=4,
                     command=lambda: self._clear_history(win),
                     cursor="hand2").pack(pady=10)

    def _clear_history(self, win):
        if messagebox.askyesno("Clear", "Clear all history?"):
            self.history = []
            save_json(HISTORY_FILE, self.history)
            win.destroy()
            self._show_history()

    def _show_menu(self):
        menu = tk.Menu(self.root, tearoff=0, bg=C["bg2"], fg=C["text"])
        menu.add_command(label="⭐ Bookmarks (Ctrl+B)", command=self._show_bookmarks)
        menu.add_command(label="📋 History (Ctrl+H)", command=self._show_history)
        menu.add_separator()
        menu.add_command(label="🏠 Set Home Page", command=self._set_home)
        menu.add_separator()
        menu.add_command(label="❌ Exit", command=self._on_close)
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def _set_home(self):
        global HOME_PAGE
        url = simpledialog.askstring("Home Page", "Enter URL:", initialvalue=HOME_PAGE)
        if url:
            HOME_PAGE = url
            self.status_lbl.config(text=f"Home set to: {url}")

    def _on_close(self):
        self.root.destroy()


def main():
    root = tk.Tk()
    NexusBrowser(root)
    root.mainloop()


if __name__ == "__main__":
    main()
