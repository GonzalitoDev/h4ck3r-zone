"""
NEXUS MOVIES v3.0 — Netflix-Style Movie Browser
Horizontal scrolling categories, hero banner, watch providers, HD posters, trailers.
"""
import os, sys, json, threading, webbrowser, random, urllib.parse
from datetime import datetime
from pathlib import Path
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import requests; HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from PIL import Image, ImageTk; HAS_PIL = True
except ImportError:
    HAS_PIL = False

API_KEY = "2dca580c2a14b55200e784d157207b4d"
BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p"

C = {
    "bg": "#0a0a0f", "bg2": "#14141f", "card": "#181825",
    "border": "#1e1e35", "text": "#e0e0e0", "dim": "#555568",
    "accent": "#e50914", "gold": "#f5c518", "green": "#46d369",
}

DATA_DIR = Path.home() / "Documents" / "NexusMovies"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FAVS = DATA_DIR / "favorites.json"


def http_get(url, params=None, t=12):
    if HAS_REQUESTS:
        r = requests.get(url, params=params, timeout=t, headers={"User-Agent": "NexusMovies/3.0"})
        return r.json(), None
    import urllib.request, urllib.parse, ssl
    if params: url += "?" + urllib.parse.urlencode(params)
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "NexusMovies/3.0"})
        with urllib.request.urlopen(req, timeout=t, context=ctx) as resp:
            return json.loads(resp.read().decode()), None
    except Exception as e:
        return {}, str(e)


def api(endpoint, params=None):
    if params is None: params = {}
    params["api_key"] = API_KEY; params["language"] = "es-MX"
    data, err = http_get(f"{BASE}{endpoint}", params)
    return data


def load_favs():
    try:
        with open(FAVS, "r", encoding="utf-8") as f: return json.load(f)
    except: return []


def save_favs(favs):
    with open(FAVS, "w", encoding="utf-8") as f: json.dump(favs, f, ensure_ascii=False)


class NexusMovies:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS MOVIES")
        self.root.geometry("1100x700")
        self.root.minsize(800, 500)
        self.root.configure(bg=C["bg"])
        self._center()
        self.root.bind("<Configure>", lambda e: self._render())

        self.favorites = load_favs()
        self.categories = {}
        self.photo_refs = []
        self.search_q = ""

        self._build()
        self.root.after(200, self._load_all)

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1100) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Top nav
        nav = tk.Frame(self.root, bg=C["bg"])
        nav.pack(fill=tk.X, padx=20, pady=(12, 0))
        tk.Label(nav, text="🎬 NEXUS MOVIES", font=("Segoe UI", 18, "bold"),
                fg=C["accent"], bg=C["bg"]).pack(side=tk.LEFT)

        # Search
        sf = tk.Frame(nav, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        sf.pack(side=tk.RIGHT)
        self.search_e = tk.Entry(sf, font=("Segoe UI", 10), bg=C["bg2"], fg=C["text"],
                                 insertbackground=C["accent"], relief=tk.FLAT, width=26, borderwidth=0)
        self.search_e.pack(side=tk.LEFT, ipady=6, padx=(12, 0))
        self.search_e.bind("<Return>", lambda e: self._search())
        tk.Button(sf, text="🔍", command=self._search, font=("Segoe UI", 11),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=12, cursor="hand2", borderwidth=0).pack(side=tk.LEFT)

        # Top row buttons
        btns = tk.Frame(nav, bg=C["bg"])
        btns.pack(side=tk.RIGHT, padx=(20, 10))
        for text, cmd in [("❤️", lambda: self._search_favs()), ("🔀", lambda: self._random_movie())]:
            tk.Button(btns, text=text, command=cmd, font=("Segoe UI", 14),
                     bg=C["bg2"], fg=C["text"], relief=tk.FLAT, padx=6, cursor="hand2",
                     borderwidth=0).pack(side=tk.LEFT, padx=2)

        # Scrollable content
        self.canvas = tk.Canvas(self.root, bg=C["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=C["bg"])
        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 50), "units"))

        # Status
        self.status = tk.Label(self.root, text="Cargando...", font=("Segoe UI", 8),
                               fg=C["dim"], bg=C["bg"])
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 6))

    def _load_all(self):
        def _run():
            sections = [
                ("🔥 TENDENCIAS", "/trending/movie/week", {}),
                ("⭐ MEJOR VALORADAS", "/movie/top_rated", {}),
                ("🆕 PRÓXIMOS ESTRENOS", "/movie/upcoming", {}),
                ("🎬 EN CARTELERA", "/movie/now_playing", {}),
            ]
            for label, ep, params in sections:
                try:
                    data = api(ep, params)
                    self.categories[label] = data.get("results", [])
                except:
                    self.categories[label] = []
            self.root.after(0, self._render)
            self.root.after(0, lambda: self.status.config(text="Listo — Buscá una película arriba", fg=C["green"]))
        threading.Thread(target=_run, daemon=True).start()

    def _render(self):
        for w in self.content.winfo_children():
            w.destroy()
        if not self.categories:
            tk.Label(self.content, text="Cargando películas...\nVerificá tu conexión a internet",
                    font=("Segoe UI", 12), fg=C["dim"], bg=C["bg"]).pack(expand=True, pady=100)
            return

        w = max(780, self.canvas.winfo_width() - 20)
        cols_per_row = max(3, w // 240)

        for label, movies in self.categories.items():
            if not movies: continue

            # Section header
            sec = tk.Frame(self.content, bg=C["bg"])
            sec.pack(fill=tk.X, padx=20, pady=(16, 0))
            tk.Label(sec, text=label, font=("Segoe UI", 13, "bold"), fg=C["text"],
                    bg=C["bg"]).pack(side=tk.LEFT)

            # Movie row (horizontal grid)
            row_f = tk.Frame(self.content, bg=C["bg"])
            row_f.pack(fill=tk.X, padx=20, pady=(6, 2))
            for i, movie in enumerate(movies[:cols_per_row]):
                if not movie.get("poster_path"): continue
                self._movie_card(row_f, movie, i)

    def _movie_card(self, parent, movie, idx):
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=1, cursor="hand2", padx=1, pady=1)
        card.pack(side=tk.LEFT, padx=(0, 10), pady=4)

        # Poster
        poster_frame = tk.Frame(card, bg=C["card"], width=180, height=270)
        poster_frame.pack()
        poster_frame.pack_propagate(False)

        title = movie.get("title", "?")[:20]
        pl = tk.Label(poster_frame, text=f"🎬\n{title}", font=("Segoe UI", 10, "bold"),
                     bg=C["bg3"], fg=C["dim"], wraplength=160, anchor="center")
        pl.place(relwidth=1, relheight=1)

        # Load poster image
        poster_url = f"{IMG}/w342{movie['poster_path']}"
        threading.Thread(target=self._load_img, args=(poster_url, pl, 180, 270), daemon=True).start()

        # Info row
        info = tk.Frame(card, bg=C["card"])
        info.pack(fill=tk.X, padx=8, pady=(4, 6))
        rating = movie.get("vote_average", 0)
        year = (movie.get("release_date", "") or "")[:4]
        tk.Label(info, text=f"⭐{rating:.1f}" if rating else "—", font=("Segoe UI", 9, "bold"),
                fg=C["gold"], bg=C["card"]).pack(side=tk.LEFT)
        tk.Label(info, text=year, font=("Segoe UI", 8), fg=C["dim"], bg=C["card"]).pack(side=tk.RIGHT)

        # Buttons row
        btns_f = tk.Frame(card, bg=C["card"])
        btns_f.pack(fill=tk.X, padx=8, pady=(0, 6))

        tk.Button(btns_f, text="▶ Ver", command=lambda m=movie: self._show_detail(m),
                 font=("Segoe UI", 8, "bold"), bg=C["accent"], fg="#fff", relief=tk.FLAT,
                 padx=10, cursor="hand2").pack(side=tk.LEFT)

        is_fav = any(f.get("id") == movie.get("id") for f in self.favorites)
        tk.Label(btns_f, text="❤️" if is_fav else "🤍", font=("Segoe UI", 12),
                bg=C["card"], fg=C["accent"] if is_fav else C["dim"], cursor="hand2").pack(side=tk.RIGHT)

        # Hover effects and click
        for w in [card, poster_frame, pl]:
            w.bind("<Button-1>", lambda e, m=movie: self._show_detail(m))
        card.bind("<Enter>", lambda e: card.config(bg=C["bg2"]))
        card.bind("<Leave>", lambda e: card.config(bg=C["card"]))

    def _load_img(self, url, label, w, h):
        try:
            if HAS_REQUESTS:
                data = requests.get(url, timeout=10, headers={"User-Agent": "NexusMovies/3.0"}).content
            else:
                import urllib.request, ssl
                ctx = ssl.create_default_context()
                req = urllib.request.Request(url, headers={"User-Agent": "NexusMovies/3.0"})
                with urllib.request.urlopen(req, timeout=10, context=ctx) as r: data = r.read()
            if HAS_PIL:
                img = Image.open(BytesIO(data)).resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_refs.append(photo)
                self.root.after(0, lambda: label.config(image=photo, text="", bg=C["card"]))
                self.root.after(0, lambda: setattr(label, 'image', photo))
        except: pass

    def _search(self):
        q = self.search_e.get().strip()
        if not q: return
        self.status.config(text=f"🔍 Buscando: {q}...", fg=C["accent2"])
        self.categories = {}

        def _run():
            data = api("/search/movie", {"query": q})
            movies = data.get("results", [])
            # Also get genres + trending for context
            try:
                data2 = api("/genre/movie/list")
            except: data2 = {}
            self.categories = {f"🔍 RESULTADOS PARA: {q.upper()}": movies}
            # Add related trending
            try:
                trending = api("/trending/movie/week", {})
                self.categories["🔥 TAMBIÉN TE PUEDE GUSTAR"] = trending.get("results", [])[:12]
            except: pass
            self.root.after(0, self._render)
            self.root.after(0, lambda: self.status.config(
                text=f"🔍 {len(movies)} resultados para '{q}'", fg=C["green"]))

        threading.Thread(target=_run, daemon=True).start()

    def _search_favs(self):
        self.categories = {"❤️ MIS FAVORITOS": load_favs()}
        self._render()
        self.status.config(text=f"❤️ {len(self.favorites)} favoritos")

    def _random_movie(self):
        all_movies = []
        for movies in self.categories.values():
            all_movies.extend(movies)
        if all_movies:
            movie = random.choice(all_movies)
            self._show_detail(movie)
            self.status.config(text=f"🎲 {movie.get('title','?')}", fg=C["accent2"])

    def _show_detail(self, movie):
        mid = movie.get("id")
        self.status.config(text="Cargando detalles...")

        def _run():
            try:
                d = api(f"/movie/{mid}")
                c = api(f"/movie/{mid}/credits")
                v = api(f"/movie/{mid}/videos")
                p = api(f"/movie/{mid}/watch/providers")
                self.root.after(0, lambda: self._detail_win(movie, d, c, v, p))
            except Exception as e:
                self.root.after(0, lambda: self.status.config(text=f"Error: {e}", fg=C["accent"]))

        threading.Thread(target=_run, daemon=True).start()

    def _detail_win(self, movie, d, c, v, p):
        win = tk.Toplevel(self.root)
        title = d.get("title", movie.get("title", "Movie"))
        win.title(title)
        win.geometry("780x650")
        win.configure(bg=C["bg"])
        win.minsize(500, 400)
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 780) // 2
        y = (win.winfo_screenheight() - 650) // 2
        win.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(win, bg=C["bg"], highlightthickness=0)
        sbar = ttk.Scrollbar(win, command=canvas.yview)
        inner = tk.Frame(canvas, bg=C["bg"])
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=760)
        canvas.configure(yscrollcommand=sbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Backdrop
        backdrop = d.get("backdrop_path")
        if backdrop:
            bg_label = tk.Label(inner, text="", bg=C["bg3"], height=10)
            bg_label.pack(fill=tk.X)
            threading.Thread(target=lambda: self._load_img(
                f"{IMG}/w780{backdrop}", bg_label, 760, 200), daemon=True).start()

        # Info
        hdr = tk.Frame(inner, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=20, pady=(16, 4))

        # Poster
        poster_path = d.get("poster_path") or movie.get("poster_path")
        poster_lbl = tk.Label(hdr, text="🎬", font=("Segoe UI", 20), bg=C["bg3"], fg=C["dim"],
                              width=14, height=8)
        poster_lbl.pack(side=tk.LEFT, padx=(0, 16))
        if poster_path:
            threading.Thread(target=lambda: self._load_img(
                f"{IMG}/w342{poster_path}", poster_lbl, 140, 210), daemon=True).start()

        info_f = tk.Frame(hdr, bg=C["bg"])
        info_f.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(info_f, text=title, font=("Segoe UI", 20, "bold"), fg=C["text"],
                bg=C["bg"], wraplength=500).pack(anchor=tk.W)

        tagline = d.get("tagline", "")
        if tagline:
            tk.Label(info_f, text=f"«{tagline}»", font=("Segoe UI", 10, "italic"),
                    fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W)

        year = (d.get("release_date", "") or "")[:4]
        rating = d.get("vote_average", 0)
        runtime = d.get("runtime", 0)
        genres = ", ".join(g["name"] for g in d.get("genres", []))
        tk.Label(info_f, text=f"{year}  •  ⭐{rating:.1f}/10  •  {runtime}min  •  {genres}",
                font=("Segoe UI", 11), fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, pady=(6, 2))

        # Watch providers
        providers = p.get("results", {}).get("AR", {}).get("flatrate", [])
        if not providers:
            providers = p.get("results", {}).get("US", {}).get("flatrate", [])
        if providers:
            pf = tk.Frame(info_f, bg=C["bg"])
            pf.pack(anchor=tk.W, pady=(8, 0))
            tk.Label(pf, text="Disponible en:", font=("Segoe UI", 8), fg=C["dim"],
                    bg=C["bg"]).pack(side=tk.LEFT)
            for prov in providers[:5]:
                tk.Label(pf, text=f"  {prov['provider_name']}", font=("Segoe UI", 8, "bold"),
                        fg=C["green"], bg=C["bg"]).pack(side=tk.LEFT)

        # Action buttons
        act_f = tk.Frame(info_f, bg=C["bg"])
        act_f.pack(anchor=tk.W, pady=(10, 0))

        trailers = [v for v in v.get("results", [])
                    if v.get("site") == "YouTube"]
        if trailers:
            tk.Button(act_f, text="▶ VER TRAILER", command=lambda: webbrowser.open(
                f"https://youtube.com/watch?v={trailers[0]['key']}"),
                     font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                     relief=tk.FLAT, padx=14, pady=6, cursor="hand2").pack(side=tk.LEFT)

        # Search on JustWatch
        tk.Button(act_f, text="🔍 Buscar dónde ver", command=lambda: webbrowser.open(
            f"https://www.justwatch.com/ar/buscar?q={urllib.parse.quote(title)}"),
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=10, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Separator
        tk.Frame(inner, bg=C["border"], height=1).pack(fill=tk.X, padx=20, pady=14)

        # Overview
        overview = d.get("overview", "Sin descripción.")
        tk.Label(inner, text="Sinopsis", font=("Segoe UI", 13, "bold"), fg=C["accent"],
                bg=C["bg"]).pack(anchor=tk.W, padx=20)
        tk.Label(inner, text=overview, font=("Segoe UI", 11), fg=C["text"],
                bg=C["bg"], wraplength=720, justify="left").pack(anchor=tk.W, padx=20, pady=(6, 12))

        # Cast
        tk.Label(inner, text="Elenco", font=("Segoe UI", 13, "bold"), fg=C["accent"],
                bg=C["bg"]).pack(anchor=tk.W, padx=20)
        cast_frame = tk.Frame(inner, bg=C["bg"])
        cast_frame.pack(fill=tk.X, padx=20, pady=(4, 8))
        for actor in c.get("cast", [])[:6]:
            ac = tk.Frame(cast_frame, bg=C["card"], highlightbackground=C["border"],
                         highlightthickness=1, padx=2, pady=2)
            ac.pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(ac, text=actor.get("name", "?"), font=("Segoe UI", 9, "bold"),
                    fg=C["text"], bg=C["card"]).pack()
            tk.Label(ac, text=actor.get("character", "?"), font=("Segoe UI", 8),
                    fg=C["dim"], bg=C["card"]).pack()

        # Budget
        budget = d.get("budget", 0); revenue = d.get("revenue", 0)
        if budget or revenue:
            tk.Label(inner, text="", bg=C["bg"]).pack()
            if budget: tk.Label(inner, text=f"💰 Presupuesto: ${budget:,}", font=("Segoe UI", 9),
                               fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20)
            if revenue: tk.Label(inner, text=f"📈 Recaudación: ${revenue:,}", font=("Segoe UI", 9),
                                fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20)


def main():
    root = tk.Tk()
    NexusMovies(root)
    root.mainloop()


if __name__ == "__main__":
    main()
