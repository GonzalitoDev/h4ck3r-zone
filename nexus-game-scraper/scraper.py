"""
NEXUS GAME SCRAPER v1.0 — Free Games Finder
Scrapes legitimate free games from itch.io, Steam, Game Jolt, Internet Archive.
100% legal — only aggregates publicly available free game listings.
"""
import os, sys, json, threading, re, time, urllib.request, urllib.parse, ssl, html, random
from datetime import datetime
from pathlib import Path
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

try:
    from bs4 import BeautifulSoup; HAS_BS4 = True
except: HAS_BS4 = False
try:
    import requests; HAS_REQ = True
except: HAS_REQ = False

C = {
    "bg": "#08080f", "bg2": "#101022", "card": "#181835",
    "border": "#202050", "text": "#d0d0e8", "dim": "#484878",
    "accent": "#a855f7", "accent2": "#c084fc",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa", "pink": "#ec4899",
}

DATA_DIR = Path.home() / "Documents" / "NexusGameScraper"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FAVS_FILE = DATA_DIR / "favorites.json"
CACHE_FILE = DATA_DIR / "cache.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def http_get(url, timeout=12):
    if HAS_REQ:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            return r.text, r.status_code, None
        except Exception as e: return "", 0, str(e)
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode(errors="ignore"), resp.status, None
    except Exception as e: return "", 0, str(e)


def http_get_json(url, timeout=10):
    text, status, err = http_get(url, timeout)
    if err or not text: return {}
    try: return json.loads(text)
    except: return {}


def load_favs():
    try:
        with open(FAVS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_favs(favs):
    with open(FAVS_FILE, "w", encoding="utf-8") as f: json.dump(favs, f, indent=2)


# ===== SCRAPERS (100% legal — public data only) =====

def scrape_itchio():
    """Scrape free games from itch.io (public browse page)."""
    games = []
    try:
        url = "https://itch.io/games/free"
        html_text, status, err = http_get(url)
        if not html_text or not HAS_BS4: return games

        soup = BeautifulSoup(html_text, "html.parser")
        for cell in soup.find_all("div", class_="game_cell")[:30]:
            try:
                title_el = cell.find("a", class_="title")
                if not title_el: continue
                title = title_el.text.strip()
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://itch.io" + link

                img = cell.find("img")
                img_url = img.get("src", "") if img else ""

                desc_el = cell.find("div", class_="game_text")
                desc = desc_el.text.strip()[:150] if desc_el else ""

                genre_el = cell.find("div", class_="game_genre")
                genre = genre_el.text.strip() if genre_el else ""

                games.append({
                    "title": title, "url": link,
                    "image": img_url, "description": desc,
                    "genre": genre or "Various",
                    "source": "itch.io", "type": "Free Game",
                })
            except: pass
    except Exception as e:
        print(f"itch.io error: {e}")
    return games


def scrape_gamejolt():
    """Scrape free games from Game Jolt."""
    games = []
    try:
        url = "https://gamejolt.com/games?price=free"
        html_text, status, err = http_get(url)
        if not html_text or not HAS_BS4: return games

        soup = BeautifulSoup(html_text, "html.parser")
        for card in soup.find_all("div", class_="game-card")[:20]:
            try:
                title_el = card.find("a", class_="game-card__title")
                if not title_el: continue
                title = title_el.text.strip()
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://gamejolt.com" + link

                img = card.find("img")
                img_url = img.get("src", "") if img else ""

                games.append({
                    "title": title, "url": link,
                    "image": img_url, "description": "",
                    "genre": "", "source": "Game Jolt", "type": "Free Game",
                })
            except: pass
    except: pass
    return games


def scrape_archive_games():
    """Scrape classic games from Internet Archive (public domain)."""
    games = []
    try:
        # Internet Archive MS-DOS games collection
        data = http_get_json(
            "https://archive.org/advancedsearch.php?"
            "q=collection:(softwarelibrary_msdos_games)&"
            "fl[]=identifier,title,year&rows=30&output=json"
        )
        docs = data.get("response", {}).get("docs", [])
        for doc in docs:
            identifier = doc.get("identifier", "")
            title = doc.get("title", "Unknown Game")
            year = doc.get("year", "")
            if identifier:
                games.append({
                    "title": title,
                    "url": f"https://archive.org/details/{identifier}",
                    "image": f"https://archive.org/services/img/{identifier}",
                    "description": f"Classic game{f' ({year})' if year else ''}",
                    "genre": "Retro/Classic",
                    "source": "Internet Archive", "type": "Public Domain",
                })
    except: pass
    return games


def scrape_steam_free():
    """Check Steam for popular free-to-play games (static known list)."""
    # Steam's page requires JavaScript. We provide a curated list of popular F2P games.
    return [
        {"title": "Counter-Strike 2", "url": "https://store.steampowered.com/app/730/",
         "image": "", "description": "Legendary tactical FPS. Free to play.",
         "genre": "FPS", "source": "Steam", "type": "Free to Play"},
        {"title": "Dota 2", "url": "https://store.steampowered.com/app/570/",
         "image": "", "description": "The most-played MOBA. Free.",
         "genre": "MOBA", "source": "Steam", "type": "Free to Play"},
        {"title": "Apex Legends", "url": "https://store.steampowered.com/app/1172470/",
         "image": "", "description": "Battle royale hero shooter. Free.",
         "genre": "Battle Royale", "source": "Steam", "type": "Free to Play"},
        {"title": "Warframe", "url": "https://store.steampowered.com/app/230410/",
         "image": "", "description": "Space ninja action. Free to play.",
         "genre": "Action", "source": "Steam", "type": "Free to Play"},
        {"title": "Destiny 2", "url": "https://store.steampowered.com/app/1085660/",
         "image": "", "description": "Sci-fi FPS MMO. Base game free.",
         "genre": "FPS/MMO", "source": "Steam", "type": "Free to Play"},
        {"title": "Team Fortress 2", "url": "https://store.steampowered.com/app/440/",
         "image": "", "description": "Classic class-based FPS. Free.",
         "genre": "FPS", "source": "Steam", "type": "Free to Play"},
        {"title": "Brawlhalla", "url": "https://store.steampowered.com/app/291550/",
         "image": "", "description": "Platform fighter like Smash Bros. Free.",
         "genre": "Fighting", "source": "Steam", "type": "Free to Play"},
        {"title": "Path of Exile", "url": "https://store.steampowered.com/app/238960/",
         "image": "", "description": "Deep ARPG like Diablo. Free.",
         "genre": "ARPG", "source": "Steam", "type": "Free to Play"},
        {"title": "Genshin Impact", "url": "https://store.epicgames.com/p/genshin-impact",
         "image": "", "description": "Open-world action RPG. Free.",
         "genre": "RPG", "source": "Epic Games", "type": "Free to Play"},
        {"title": "Fortnite", "url": "https://store.epicgames.com/p/fortnite",
         "image": "", "description": "Battle royale phenomenon. Free.",
         "genre": "Battle Royale", "source": "Epic Games", "type": "Free to Play"},
        {"title": "Rocket League", "url": "https://store.epicgames.com/p/rocket-league",
         "image": "", "description": "Soccer with cars. Free to play.",
         "genre": "Sports", "source": "Epic Games", "type": "Free to Play"},
        {"title": "Fall Guys", "url": "https://store.epicgames.com/p/fall-guys",
         "image": "", "description": "Battle royale party game. Free.",
         "genre": "Party", "source": "Epic Games", "type": "Free to Play"},
    ]


def scrape_all():
    """Run all scrapers and return combined results."""
    all_games = []
    all_games.extend(scrape_steam_free())
    all_games.extend(scrape_archive_games())

    if HAS_BS4:
        all_games.extend(scrape_itchio())
        all_games.extend(scrape_gamejolt())

    # Remove duplicates by URL
    seen = set()
    unique = []
    for g in all_games:
        if g["url"] not in seen:
            seen.add(g["url"])
            unique.append(g)

    return unique


class NexusGameScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS GAME SCRAPER — Free Games Finder")
        self.root.geometry("880x620")
        self.root.minsize(650, 450)
        self.root.configure(bg=C["bg"])
        self._center()

        self.favorites = load_favs()
        self.games = []
        self.photo_refs = []
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 880) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🎮 NEXUS GAME SCRAPER", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Free Games Finder | 100% Legal", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Action buttons
        btn_f = tk.Frame(self.root, bg=C["bg"])
        btn_f.pack(fill=tk.X, padx=16, pady=(6, 0))
        self.scrape_btn = tk.Button(btn_f, text="🔍 SEARCH FREE GAMES", command=self._scrape,
                                    font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                                    relief=tk.FLAT, padx=18, pady=5, cursor="hand2")
        self.scrape_btn.pack(side=tk.LEFT)
        tk.Button(btn_f, text="❤️ Favorites", command=self._show_favs,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_f, text="📄 Export CSV", command=self._export,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        # Source filter
        self.source_var = tk.StringVar(value="All")
        src_cb = ttk.Combobox(btn_f, textvariable=self.source_var,
                              values=["All","Steam","Epic Games","itch.io","Game Jolt","Internet Archive"],
                              state="readonly", font=("Segoe UI", 9), width=14)
        src_cb.pack(side=tk.RIGHT, padx=4)
        src_cb.bind("<<ComboboxSelected>>", lambda e: self._filter())
        tk.Label(btn_f, text="Source:", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"]).pack(side=tk.RIGHT, padx=2)

        # Games grid
        self.canvas = tk.Canvas(self.root, bg=C["bg"], highlightthickness=0)
        self.sbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.card_f = tk.Frame(self.canvas, bg=C["bg"])
        self.card_f.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.card_f, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 40), "units"))

        self.status_lbl = tk.Label(self.root, text="Ready — Click SEARCH FREE GAMES",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

        # Load cache
        try:
            with open(CACHE_FILE) as f: self.games = json.load(f)[:50]
            if self.games: self._render_games()
        except: pass

    def _scrape(self):
        self.scrape_btn.config(text="⏳ SCRAPING...", state=tk.DISABLED, bg=C["bg2"], fg=C["dim"])
        self.status_lbl.config(text="🔍 Searching free games from 5 sources...", fg=C["accent"])

        def _run():
            games = scrape_all()
            self.games = games
            with open(CACHE_FILE, "w") as f: json.dump(games, f, indent=2)
            self.root.after(0, self._scrape_done)

        threading.Thread(target=_run, daemon=True).start()

    def _scrape_done(self):
        self.scrape_btn.config(text="🔍 SEARCH FREE GAMES", state=tk.NORMAL, bg=C["accent"], fg="#fff")
        self._render_games()
        self.status_lbl.config(text=f"✅ Found {len(self.games)} free games from 5 sources",
                               fg=C["green"])

    def _render_games(self):
        for w in self.card_f.winfo_children(): w.destroy()

        filtered = self.games
        source = self.source_var.get()
        if source != "All":
            filtered = [g for g in filtered if g.get("source") == source]

        if not filtered:
            tk.Label(self.card_f, text="No games found. Click SEARCH.",
                    font=("Segoe UI", 12), fg=C["dim"], bg=C["bg"]).pack(expand=True, pady=80)
            return

        w = max(700, self.canvas.winfo_width() - 20)
        cols = max(1, w // 260)

        for i, game in enumerate(filtered[:60]):
            row, col = i // cols, i % cols
            pad = 8
            x = col * (250 + pad) + pad
            y = row * (200 + pad) + pad

            card = tk.Frame(self.card_f, bg=C["card"], highlightbackground=C["border"],
                           highlightthickness=1, cursor="hand2")
            card.place(x=x, y=y, width=250, height=200)

            # Source badge
            src_color = {"Steam":"#1a9fff","Epic Games":"#121212","itch.io":"#fa5c5c",
                        "Game Jolt":"#2f7b3c","Internet Archive":"#f59e0b"}.get(game.get("source",""),C["border"])
            tk.Label(card, text=f" {game.get('source','')} ", font=("Segoe UI", 7, "bold"),
                    fg="#fff", bg=src_color).place(x=4, y=4)

            # Type
            tk.Label(card, text=game.get("type", "Free"), font=("Segoe UI", 7),
                    fg=C["green"], bg=C["card"]).place(relx=1.0, x=-4, y=4, anchor="ne")

            # Title
            tk.Label(card, text=game.get("title", "?")[:35], font=("Segoe UI", 10, "bold"),
                    fg=C["text"], bg=C["card"], wraplength=230, anchor="w").place(x=8, y=28)

            # Description
            desc = game.get("description", "")[:100]
            if desc:
                tk.Label(card, text=desc, font=("Segoe UI", 8),
                        fg=C["dim"], bg=C["card"], wraplength=230, anchor="w", justify="left").place(x=8, y=65)

            # Genre
            genre = game.get("genre", "")
            if genre:
                tk.Label(card, text=genre[:20], font=("Segoe UI", 8),
                        fg=C["blue"], bg=C["card"]).place(x=8, y=140)

            # Play button
            play_btn = tk.Label(card, text="▶ PLAY / DOWNLOAD", font=("Segoe UI", 9, "bold"),
                               fg=C["accent"], bg=C["card"], cursor="hand2")
            play_btn.place(x=8, y=165)
            play_btn.bind("<Button-1>", lambda e, u=game.get("url"): __import__('webbrowser').open(u))
            card.bind("<Button-1>", lambda e, u=game.get("url"): __import__('webbrowser').open(u))

            # Heart button
            is_fav = any(f.get("url") == game.get("url") for f in self.favorites)
            heart = tk.Label(card, text="❤️" if is_fav else "🤍", font=("Segoe UI", 11),
                           bg=C["card"], fg=C["red"] if is_fav else C["dim"], cursor="hand2")
            heart.place(relx=1.0, x=-8, y=165, anchor="e")
            heart.bind("<Button-1>", lambda e, g=game: self._toggle_fav(g))

    def _filter(self):
        self._render_games()

    def _show_favs(self):
        self.games = load_favs()
        self.source_var.set("All")
        self._render_games()
        self.status_lbl.config(text=f"❤️ {len(self.games)} favorite games", fg=C["red"])

    def _toggle_fav(self, game):
        idx = next((i for i, f in enumerate(self.favorites) if f.get("url") == game.get("url")), -1)
        if idx >= 0: self.favorites.pop(idx)
        else: self.favorites.append(game)
        save_favs(self.favorites)
        self._render_games()

    def _export(self):
        if not self.games: return
        fp = filedialog.asksaveasfilename(defaultextension=".csv",
                                          filetypes=[("CSV", "*.csv")], initialfile="free_games.csv")
        if not fp: return
        import csv
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Title", "Source", "Genre", "Type", "URL"])
            for g in self.games:
                w.writerow([g.get("title",""), g.get("source",""), g.get("genre",""),
                           g.get("type",""), g.get("url","")])
        messagebox.showinfo("Exported", f"CSV saved to:\n{fp}")


def main():
    root = tk.Tk()
    NexusGameScraper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
