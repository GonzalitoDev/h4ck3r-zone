"""
NEXUS DATA SCRAPER v1.0 — Web Data Extraction Tool
Scrapes emails, phones, links, images, tables, metadata, text from websites.
Export to CSV, JSON, Excel. 100% real HTTP requests.
"""
import os, sys, json, threading, csv, re, time, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path
from io import BytesIO
from collections import defaultdict

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

try:
    from bs4 import BeautifulSoup; HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
try:
    import requests; HAS_REQ = True
except ImportError:
    HAS_REQ = False

C = {
    "bg": "#0a080f", "bg2": "#141020", "card": "#1a1530",
    "border": "#2a2050", "text": "#d8d4e8", "dim": "#585070",
    "accent": "#a855f7", "accent2": "#c084fc",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "blue": "#60a5fa", "gold": "#fbbf24",
}

DATA_DIR = Path.home() / "Documents" / "NexusScraper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def http_get(url, timeout=12):
    """Get page content. Returns (html, error)."""
    if HAS_REQ:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            return r.text, None
        except Exception as e:
            return "", str(e)
    else:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode(errors="ignore"), None
        except Exception as e:
            return "", str(e)


def scrape_all(html, base_url):
    """Run all scrapers on HTML. Returns dict of results."""
    if not HAS_BS4:
        return {"error": "BeautifulSoup4 not installed. Run: pip install beautifulsoup4"}

    soup = BeautifulSoup(html, "html.parser")
    results = {}

    # Emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    results["emails"] = list(set(re.findall(email_pattern, html)))[:50]

    # Phone numbers
    phone_pattern = r'(?:\+?(\d{1,3})[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    results["phones"] = list(set(re.findall(phone_pattern, html)))[:30]

    # Links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            href = urllib.parse.urljoin(base_url, href)
        text = a.get_text(strip=True)[:50]
        links.append({"url": href, "text": text})
    results["links"] = links[:100]

    # Internal vs external links
    domain = urllib.parse.urlparse(base_url).netloc
    internal = [l for l in links if domain in l["url"]]
    external = [l for l in links if domain not in l["url"]]
    results["internal_links"] = internal[:50]
    results["external_links"] = external[:50]

    # Images
    images = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("/"):
            src = urllib.parse.urljoin(base_url, src)
        alt = img.get("alt", "")
        images.append({"url": src[:200], "alt": alt[:100]})
    results["images"] = images[:50]

    # Social media links
    social_domains = ["facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
                      "youtube.com", "github.com", "tiktok.com", "discord.gg", "telegram",
                      "whatsapp.com", "reddit.com", "pinterest.com", "snapchat.com",
                      "twitch.tv", "medium.com", "t.me"]
    social = [l for l in links if any(d in l["url"].lower() for d in social_domains)]
    results["social"] = social[:20]

    # Metadata
    meta = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name", tag.get("property", tag.get("http-equiv", ""))).lower()
        content = tag.get("content", "")
        if name and content:
            meta[name] = content
    results["metadata"] = meta

    # Title
    title_tag = soup.find("title")
    results["title"] = title_tag.get_text(strip=True) if title_tag else "No title"

    # Headings structure
    headings = {}
    for level in range(1, 7):
        hs = soup.find_all(f"h{level}")
        headings[f"h{level}"] = [h.get_text(strip=True)[:100] for h in hs[:10]]
    results["headings"] = headings

    # Tables
    tables = []
    for table in soup.find_all("table")[:10]:
        rows = []
        for tr in table.find_all("tr")[:20]:
            cols = [td.get_text(strip=True)[:50] for td in tr.find_all(["td", "th"])]
            if cols:
                rows.append(cols)
        if rows:
            tables.append(rows)
    results["tables"] = tables

    # Forms
    forms = []
    for form in soup.find_all("form"):
        action = form.get("action", "")
        method = form.get("method", "GET").upper()
        inputs = []
        for inp in form.find_all("input"):
            inputs.append({
                "name": inp.get("name", ""),
                "type": inp.get("type", "text"),
                "placeholder": inp.get("placeholder", ""),
            })
        forms.append({"action": action, "method": method, "inputs": inputs})
    results["forms"] = forms[:5]

    # Page stats
    results["stats"] = {
        "total_links": len(links),
        "total_images": len(images),
        "total_forms": len(forms),
        "total_tables": len(tables),
        "page_size_kb": len(html) / 1024,
    }

    return results


class NexusScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS DATA SCRAPER")
        self.root.geometry("900x620")
        self.root.minsize(700, 480)
        self.root.configure(bg=C["bg"])
        self._center()
        self.last_results = {}
        self.last_url = ""
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
        tk.Label(hdr, text="🕷️ NEXUS DATA SCRAPER", font=("Segoe UI", 16, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)

        # URL input
        url_f = tk.Frame(self.root, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        url_f.pack(fill=tk.X, padx=16, pady=(8, 0))
        inner = tk.Frame(url_f, bg=C["bg2"])
        inner.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(inner, text="URL:", font=("Segoe UI", 9, "bold"), fg=C["dim"], bg=C["bg2"]).pack(side=tk.LEFT)
        self.url_e = tk.Entry(inner, font=("Consolas", 10), bg=C["bg"], fg=C["text"],
                              insertbackground=C["accent"], relief=tk.FLAT, width=50, borderwidth=0)
        self.url_e.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True, ipady=5)
        self.url_e.insert(0, "https://")
        self.url_e.bind("<Return>", lambda e: self._scrape())
        self.scrape_btn = tk.Button(inner, text="🕷️ SCRAPE", command=self._scrape,
                                    font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                                    relief=tk.FLAT, padx=18, pady=5, cursor="hand2")
        self.scrape_btn.pack(side=tk.LEFT)

        # Results notebook
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))
        st2 = ttk.Style()
        st2.theme_use("clam")
        st2.configure("TNotebook", background=C["bg"], borderwidth=0)
        st2.configure("TNotebook.Tab", background=C["bg2"], foreground=C["dim"], padding=[10, 4], font=("Segoe UI", 9))

        self.tabs = {}
        for label, icon in [
            ("Overview", "📊"), ("Emails", "📧"), ("Phones", "📱"),
            ("Links", "🔗"), ("Images", "🖼️"), ("Social", "🌐"),
            ("Metadata", "📋"), ("Tables", "📈"), ("Forms", "📝"),
        ]:
            tab = tk.Frame(nb, bg=C["bg"])
            nb.add(tab, text=f"{icon} {label}")
            tree = ttk.Treeview(tab, show="headings", selectmode="extended")
            tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            self.tabs[label.lower()] = {"frame": tab, "tree": tree}

        # Toolbar
        tbar = tk.Frame(self.root, bg=C["bg2"], height=28)
        tbar.pack(fill=tk.X, side=tk.BOTTOM)
        tbar.pack_propagate(False)
        tk.Button(tbar, text="📄 Export CSV", command=lambda: self._export("csv"),
                 font=("Segoe UI", 8), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=10, cursor="hand2").pack(side=tk.LEFT, padx=4, pady=2)
        tk.Button(tbar, text="📋 Export JSON", command=lambda: self._export("json"),
                 font=("Segoe UI", 8), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=10, cursor="hand2").pack(side=tk.LEFT, pady=2)
        self.status_lbl = tk.Label(tbar, text="Ready — Enter URL and click SCRAPE",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg2"])
        self.status_lbl.pack(side=tk.RIGHT, padx=12, pady=2)

    def _scrape(self):
        url = self.url_e.get().strip()
        if not url.startswith("http"):
            url = "https://" + url
            self.url_e.delete(0, tk.END)
            self.url_e.insert(0, url)

        self.last_url = url
        self.scrape_btn.config(text="⏳ Scraping...", state=tk.DISABLED, bg=C["bg2"], fg=C["dim"])
        self.status_lbl.config(text=f"Scraping {url}...", fg=C["blue"])

        # Clear all trees
        for tab in self.tabs.values():
            tab["tree"].delete(*tab["tree"].get_children())

        def _run():
            html, err = http_get(url)
            if err:
                self.root.after(0, lambda: self._error(f"HTTP Error: {err}"))
                return

            try:
                results = scrape_all(html, url)
                self.last_results = results
                self.root.after(0, lambda: self._show_results(results))
            except Exception as e:
                self.root.after(0, lambda: self._error(f"Scrape Error: {e}"))

        threading.Thread(target=_run, daemon=True).start()

    def _error(self, msg):
        self.scrape_btn.config(text="🕷️ SCRAPE", state=tk.NORMAL, bg=C["accent"], fg="#fff")
        self.status_lbl.config(text=msg[:80], fg=C["red"])

    def _show_results(self, r):
        self.scrape_btn.config(text="🕷️ SCRAPE", state=tk.NORMAL, bg=C["accent"], fg="#fff")
        total_items = sum(len(v) if isinstance(v, list) else 1 for v in r.values())
        self.status_lbl.config(text=f"Done — {total_items} items scraped from {self.last_url[:50]}",
                               fg=C["green"])

        # Overview tab
        tree = self.tabs["overview"]["tree"]
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"],
                     rowheight=24, font=("Consolas", 8))
        cols = ("item", "count")
        tree["columns"] = cols
        tree.heading("item", text="Category"); tree.heading("count", text="Count")
        tree.column("item", width=200); tree.column("count", width=100)
        stats = r.get("stats", {})
        overview = [
            ("Title", r.get("title", "")),
            ("Total Links", str(len(r.get("links", [])))),
            ("Total Images", str(len(r.get("images", [])))),
            ("Emails Found", str(len(r.get("emails", [])))),
            ("Phones Found", str(len(r.get("phones", [])))),
            ("Social Media", str(len(r.get("social", [])))),
            ("Forms", str(len(r.get("forms", [])))),
            ("Tables", str(len(r.get("tables", [])))),
            ("Page Size", f"{stats.get('page_size_kb', 0):.1f} KB"),
        ]
        for item, count in overview:
            tree.insert("", tk.END, values=(item, count))

        # Emails
        self._fill_list("emails", r.get("emails", []), ["email"], ["Email"])

        # Phones
        self._fill_list("phones", r.get("phones", []), ["phone"], ["Phone"])

        # Links
        self._fill_dict_list("links", r.get("links", []),
                            ["url", "text"], ["URL", "Text"], {"url": 400, "text": 250})

        # Images
        self._fill_dict_list("images", r.get("images", []),
                            ["url", "alt"], ["URL", "Alt"], {"url": 400, "alt": 250})

        # Social
        self._fill_dict_list("social", r.get("social", []),
                            ["url", "text"], ["URL", "Text"], {"url": 400, "text": 250})

        # Metadata
        meta = r.get("metadata", {})
        meta_tree = self.tabs["metadata"]["tree"]
        meta_tree["columns"] = ("key", "value")
        meta_tree.heading("key", text="Key"); meta_tree.heading("value", text="Value")
        meta_tree.column("key", width=200); meta_tree.column("value", width=450)
        for k, v in meta.items():
            meta_tree.insert("", tk.END, values=(k[:100], v[:200]))

        # Tables
        # Show first table in table tab
        tables = r.get("tables", [])
        table_tree = self.tabs["tables"]["tree"]
        if tables and tables[0]:
            first_table = tables[0]
            max_cols = max(len(row) for row in first_table) if first_table else 1
            cols_names = [f"Col{i+1}" for i in range(max_cols)]
            table_tree["columns"] = cols_names
            for i, col in enumerate(cols_names):
                table_tree.heading(col, text=col)
                table_tree.column(col, width=150)
            for row in first_table[:50]:
                padded = row + [""] * (max_cols - len(row))
                table_tree.insert("", tk.END, values=padded)

        # Forms
        forms = r.get("forms", [])
        form_tree = self.tabs["forms"]["tree"]
        form_tree["columns"] = ("action", "method", "inputs")
        form_tree.heading("action", text="Action"); form_tree.heading("method", text="Method")
        form_tree.heading("inputs", text="Inputs")
        form_tree.column("action", width=250); form_tree.column("method", width=60)
        form_tree.column("inputs", width=300)
        for form in forms:
            inputs_str = ", ".join(
                f"{i['name'] or '?'}({i['type']})" for i in form.get("inputs", [])[:5]
            )
            form_tree.insert("", tk.END, values=(form.get("action", ""),
                                                  form.get("method", ""), inputs_str))

    def _fill_list(self, tab_key, items, columns, headings):
        tree = self.tabs[tab_key]["tree"]
        tree["columns"] = columns
        for i, col in enumerate(columns):
            tree.heading(col, text=headings[i])
            tree.column(col, width=500)
        for item in items:
            tree.insert("", tk.END, values=(item,))

    def _fill_dict_list(self, tab_key, items, columns, headings, widths=None):
        tree = self.tabs[tab_key]["tree"]
        tree["columns"] = columns
        for i, col in enumerate(columns):
            tree.heading(col, text=headings[i])
            tree.column(col, width=widths[col] if widths else 250)
        for item in items:
            vals = [item.get(c, "") for c in columns]
            tree.insert("", tk.END, values=vals)

    def _export(self, fmt):
        if not self.last_results:
            messagebox.showinfo("No data", "Scrape a URL first.")
            return

        if fmt == "csv":
            fp = filedialog.asksaveasfilename(defaultextension=".csv",
                                              filetypes=[("CSV", "*.csv")],
                                              initialfile="scrape_export.csv")
            if not fp: return
            with open(fp, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Category", "Data"])
                for cat in ["emails", "phones"]:
                    for item in self.last_results.get(cat, []):
                        writer.writerow([cat, item])
                for link in self.last_results.get("links", []):
                    writer.writerow(["link", f"{link['url']} | {link['text']}"])
            messagebox.showinfo("Exported", f"CSV saved to:\n{fp}")

        elif fmt == "json":
            fp = filedialog.asksaveasfilename(defaultextension=".json",
                                              filetypes=[("JSON", "*.json")],
                                              initialfile="scrape_export.json")
            if not fp: return
            export = {
                "url": self.last_url,
                "date": datetime.now().isoformat(),
                "results": self.last_results,
            }
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"JSON saved to:\n{fp}")


def main():
    root = tk.Tk()
    NexusScraper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
