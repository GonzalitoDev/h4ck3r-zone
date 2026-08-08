"""
NEXUS MOVIES v2.0 — Movie Browser & Discovery
TMDB API. Netflix-style UI. Trending, search, genres, favorites, cast, trailers.
"""
import os, sys, json, threading, webbrowser, time
from datetime import datetime
from pathlib import Path
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

API_KEY = "2dca580c2a14b55200e784d157207b4d"
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

C = {
    "bg": "#0a0a0f", "bg2": "#14141f", "bg3": "#0d0d18",
    "border": "#1e1e35", "text": "#e0e0e0", "dim": "#555568",
    "accent": "#e50914", "accent2": "#ff4757",
    "gold": "#f5c518", "green": "#46d369",
    "card": "#181825",
}

DATA_DIR = Path.home() / "Documents" / "NexusMovies"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FAVS_FILE = DATA_DIR / "favorites.json"


def http_get(url, params=None, timeout=12):
    """Make HTTP GET with error handling."""
    if HAS_REQUESTS:
        try:
            r = requests.get(url, params=params, timeout=timeout,
                           headers={"User-Agent": "NexusMovies/2.0"})
            return r.json() if r.status_code == 200 else {}
        except Exception as e:
            raise Exception(f"Network error: {e}")
    else:
        import urllib.request, urllib.parse, urllib.error, ssl
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers={"User-Agent": "NexusMovies/2.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            raise Exception(f"Network error: {e}")


def api_get(endpoint, params=None):
    if params is None:
        params = {}
    params["api_key"] = API_KEY
    params["language"] = "es-MX"
    return http_get(f"{BASE_URL}{endpoint}", params)


def load_favs():
    try:
        with open(FAVS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_favs(favs):
    with open(FAVS_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False)


class NexusMovies:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS MOVIES")
        self.root.geometry("1024x680")
        self.root.minsize(780, 500)
        self.root.configure(bg=C["bg"])
        self._center()

        self.favorites = load_favs()
        self.movies = []
        self.photo_refs = []
        self.current_page = 1
        self.current_mode = "trending"
        self.current_genre = None
        self.genres = {}

        self._build()
        self.root.after(300, self._load_genres_and_trending)

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1024) // 2
        y = (self.root.winfo_screenheight() - 680) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🎬 NEXUS MOVIES", font=("Segoe UI", 16, "bold"),
                fg=C["accent"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="v2.0 | Movie Browser", font=("Segoe UI", 8),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Search
        s2 = tk.Frame(hdr, bg=C["bg"]); s2.pack(side=tk.RIGHT)
        self.search_e = tk.Entry(s2, font=("Segoe UI", 10), bg=C["bg3"], fg=C["text"],
                                 insertbackground=C["accent"], relief=tk.FLAT, width=22)
        self.search_e.pack(side=tk.LEFT, ipady=4)
        self.search_e.bind("<Return>", lambda e: self._search())
        tk.Button(s2, text="🔍", command=self._search, font=("Segoe UI", 10),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=10, cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Categories
        cat_f = tk.Frame(self.root, bg=C["bg"])
        cat_f.pack(fill=tk.X, padx=16, pady=(6, 0))
        categories = [
            ("🔥 Trending", "trending"),
            ("⭐ Top", "top"),
            ("🆕 Próximos", "upcoming"),
            ("🎬 Cartelera", "now"),
            ("❤️ Favs", "favs"),
        ]
        self.cat_btns = {}
        for text, mode in categories:
            btn = tk.Button(cat_f, text=text, command=lambda m=mode: self._switch_mode(m),
                           font=("Segoe UI", 9), bg=C["bg2"], fg=C["dim"], relief=tk.FLAT,
                           padx=12, pady=5, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=1)
            self.cat_btns[mode] = btn

        # Genre filter
        gf = tk.Frame(self.root, bg=C["bg"])
        gf.pack(fill=tk.X, padx=16, pady=(4, 0))
        tk.Label(gf, text="Género:", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT)
        self.genre_var = tk.StringVar(value="All")
        self.genre_cb = ttk.Combobox(gf, textvariable=self.genre_var, state="readonly",
                                     font=("Segoe UI", 8), width=14)
        self.genre_cb.pack(side=tk.LEFT, padx=4)
        self.genre_cb.bind("<<ComboboxSelected>>", lambda e: self._filter_genre())

        # Grid area
        self.grid_f = tk.Frame(self.root, bg=C["bg"])
        self.grid_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))

        self.canvas = tk.Canvas(self.grid_f, bg=C["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.grid_f, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=C["bg"])
        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 60), "units"))

        # Status
        self.status_lbl = tk.Label(self.root, text="Cargando...", font=("Segoe UI", 8),
                                   fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

    def _set_status(self, msg, color=None):
        self.status_lbl.config(text=msg, fg=color or C["dim"])

    def _load_genres_and_trending(self):
        # Load genres
        def _run():
            try:
                data = api_get("/genre/movie/list")
                genres = data.get("genres", [])
                self.genres = {g["name"]: g["id"] for g in genres}
                self.root.after(0, lambda: self.genre_cb.configure(
                    values=["All"] + sorted(self.genres.keys())))
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Error géneros: {e}", "#ff3d71"))
            # Load trending
            self._switch_mode("trending")
        threading.Thread(target=_run, daemon=True).start()

    def _switch_mode(self, mode):
        self.current_mode = mode
        self.current_page = 1
        self.movies = []
        self.genre_var.set("All")
        self.current_genre = None

        for m, btn in self.cat_btns.items():
            btn.config(bg=C["bg2"], fg=C["dim"])
        if mode in self.cat_btns:
            self.cat_btns[mode].config(bg=C["accent"], fg="#fff")

        endpoints = {
            "trending": "/trending/movie/week",
            "top": "/movie/top_rated",
            "upcoming": "/movie/upcoming",
            "now": "/movie/now_playing",
        }

        if mode == "favs":
            self.movies = load_favs()
            self._render_grid()
            self._set_status(f"❤️ {len(self.movies)} favoritos")
            return

        if mode in endpoints:
            self._set_status("Cargando películas...")
            self._render_grid()  # show loading
            threading.Thread(target=lambda ep=endpoints[mode]: self._fetch_movies(ep), daemon=True).start()

    def _fetch_movies(self, endpoint):
        try:
            data = api_get(endpoint, {"page": self.current_page})
            new_movies = data.get("results", [])
            if self.current_page == 1:
                self.movies = new_movies
            else:
                self.movies.extend(new_movies)
            self.root.after(0, self._render_grid)
            self.root.after(0, lambda: self._set_status(
                f"{len(self.movies)} películas cargadas", C["green"]))
        except Exception as e:
            self.root.after(0, self._render_grid)
            self.root.after(0, lambda: self._set_status(
                f"Error: {e}. ¿Tenés internet?", "#ff3d71"))

    def _search(self):
        query = self.search_e.get().strip()
        if not query:
            return
        self.current_mode = "search"
        self._set_status(f"🔍 Buscando: {query}...")
        self.movies = []
        for m, btn in self.cat_btns.items():
            btn.config(bg=C["bg2"], fg=C["dim"])
        self._render_grid()

        def _run():
            try:
                data = api_get("/search/movie", {"query": query})
                self.movies = data.get("results", [])
                self.root.after(0, self._render_grid)
                self.root.after(0, lambda: self._set_status(
                    f"🔍 {len(self.movies)} resultados para '{query}'", C["green"]))
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Error: {e}", "#ff3d71"))

        threading.Thread(target=_run, daemon=True).start()

    def _filter_genre(self):
        genre_name = self.genre_var.get()
        if genre_name == "All":
            self.current_genre = None
        else:
            self.current_genre = self.genres.get(genre_name)

        if self.current_mode in ("favs",):
            return

        self.movies = []
        self.current_page = 1
        self._set_status(f"Cargando género: {genre_name}...")

        def _run():
            try:
                params = {"sort_by": "popularity.desc", "page": self.current_page}
                if self.current_genre:
                    params["with_genres"] = str(self.current_genre)
                data = api_get("/discover/movie", params)
                self.movies = data.get("results", [])
                self.root.after(0, self._render_grid)
                self.root.after(0, lambda: self._set_status(
                    f"{len(self.movies)} películas en {genre_name}", C["green"]))
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Error: {e}", "#ff3d71"))

        threading.Thread(target=_run, daemon=True).start()

    def _render_grid(self):
        for widget in self.scroll_content.winfo_children():
            widget.destroy()
        self.photo_refs.clear()

        canvas_w = self.canvas.winfo_width() or 900
        cols = max(2, canvas_w // 170)
        pad = 8
        movies = self.movies[:80]

        # Show error/empty state
        if not movies:
            tk.Label(self.scroll_content, text="No se encontraron películas\nVerificá tu conexión a internet",
                    font=("Segoe UI", 12), fg=C["dim"], bg=C["bg"]).pack(expand=True, pady=80)
            return

        for i, movie in enumerate(movies):
            if not movie.get("poster_path"):
                continue
            row = i // cols
            col = i % cols
            x = col * (160 + pad) + pad
            y = row * (285 + pad) + pad

            card = tk.Frame(self.scroll_content, bg=C["card"],
                           highlightbackground=C["border"], highlightthickness=1, cursor="hand2")
            card.place(x=x, y=y, width=160, height=285)

            # Poster placeholder with title
            title = movie.get("title", "?")[:22]
            pl = tk.Label(card, text=f"🎬\n{title}", font=("Segoe UI", 9, "bold"),
                         bg=C["bg3"], fg=C["dim"], height=12, wraplength=140, anchor="center")
            pl.pack(fill=tk.X)

            # Load poster
            poster_url = f"{IMG_BASE}{movie['poster_path']}"
            threading.Thread(target=self._load_poster,
                           args=(poster_url, pl), daemon=True).start()

            # Rating
            rating = movie.get("vote_average", 0)
            tk.Label(card, text=f"⭐ {rating:.1f}" if rating else "—",
                    font=("Segoe UI", 8, "bold"), fg=C["gold"], bg=C["card"]).pack(pady=(2, 0))

            # Year
            year = (movie.get("release_date", "") or "")[:4] or "—"
            tk.Label(card, text=year, font=("Segoe UI", 8), fg=C["dim"], bg=C["card"]).pack()

            # Heart
            is_fav = any(f.get("id") == movie.get("id") for f in self.favorites)
            fav_lbl = tk.Label(card, text="❤️" if is_fav else "🤍",
                              font=("Segoe UI", 11), bg=C["card"],
                              fg=C["accent"] if is_fav else C["dim"], cursor="hand2")
            fav_lbl.pack(pady=(2, 0))
            fav_lbl.bind("<Button-1>", lambda e, m=movie: self._toggle_fav(m))
            pl.bind("<Button-1>", lambda e, m=movie: self._show_detail(m))
            card.bind("<Button-1>", lambda e, m=movie: self._show_detail(m))

        # Load more
        if self.current_mode not in ("favs", "search") and len(self.movies) >= 20:
            y_more = (max(0, (len(movies) - 1) // cols) + 1) * (285 + pad) + pad
            tk.Button(self.scroll_content, text="▼ Cargar Más", command=self._load_more,
                     font=("Segoe UI", 10, "bold"), bg=C["bg2"], fg=C["text"],
                     relief=tk.FLAT, padx=20, pady=8, cursor="hand2").place(
                x=pad, y=y_more, width=canvas_w - 2 * pad)

    def _load_poster(self, url, label):
        try:
            if HAS_REQUESTS:
                r = requests.get(url, timeout=8, headers={"User-Agent": "NexusMovies/2.0"})
                data = r.content
            else:
                import urllib.request, ssl
                ctx = ssl.create_default_context()
                req = urllib.request.Request(url, headers={"User-Agent": "NexusMovies/2.0"})
                with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                    data = resp.read()

            if HAS_PIL:
                img = Image.open(BytesIO(data))
                img = img.resize((160, 240), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_refs.append(photo)
                self.root.after(0, lambda: label.config(image=photo, text="",
                                                         height=240, bg=C["card"]))
                self.root.after(0, lambda: setattr(label, 'image', photo))
            else:
                self.root.after(0, lambda: label.config(text="🎬", font=("Segoe UI", 24)))
        except:
            pass

    def _load_more(self):
        self.current_page += 1
        self._set_status(f"Cargando página {self.current_page}...")
        endpoints = {
            "trending": "/trending/movie/week",
            "top": "/movie/top_rated",
            "upcoming": "/movie/upcoming",
            "now": "/movie/now_playing",
        }
        if self.current_mode in endpoints:
            threading.Thread(target=lambda: self._fetch_movies(endpoints[self.current_mode]),
                           daemon=True).start()

    def _toggle_fav(self, movie):
        idx = next((i for i, f in enumerate(self.favorites) if f.get("id") == movie.get("id")), -1)
        if idx >= 0:
            self.favorites.pop(idx)
        else:
            self.favorites.append({
                "id": movie.get("id"), "title": movie.get("title"),
                "poster_path": movie.get("poster_path"),
                "vote_average": movie.get("vote_average"),
                "release_date": movie.get("release_date"),
                "overview": movie.get("overview"),
            })
        save_favs(self.favorites)
        if self.current_mode == "favs":
            self.movies = self.favorites
        self._render_grid()

    def _show_detail(self, movie):
        mid = movie.get("id")
        self._set_status("Cargando detalles...", C["accent2"])

        def _run():
            try:
                details = api_get(f"/movie/{mid}")
                credits = api_get(f"/movie/{mid}/credits")
                videos = api_get(f"/movie/{mid}/videos")
                self.root.after(0, lambda: self._detail_window(movie, details, credits, videos))
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Error: {e}", "#ff3d71"))

        threading.Thread(target=_run, daemon=True).start()

    def _detail_window(self, movie, details, credits, videos):
        win = tk.Toplevel(self.root)
        title = details.get("title", movie.get("title", "Movie"))
        win.title(title)
        win.geometry("680x580")
        win.configure(bg=C["bg"])
        win.minsize(450, 350)
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 680) // 2
        y = (win.winfo_screenheight() - 580) // 2
        win.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(win, bg=C["bg"], highlightthickness=0)
        sbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=C["bg"])
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw", width=660)
        canvas.configure(yscrollcommand=sbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0)
        sbar.pack(side=tk.RIGHT, fill=tk.Y)

        year = (details.get("release_date", "") or "")[:4]
        rating = details.get("vote_average", 0)
        runtime = details.get("runtime", 0)
        genres = ", ".join(g["name"] for g in details.get("genres", []))
        overview = details.get("overview", "Sin descripción.")
        budget = details.get("budget", 0)
        revenue = details.get("revenue", 0)
        tagline = details.get("tagline", "")

        tk.Label(content, text=title, font=("Segoe UI", 18, "bold"), fg=C["text"],
                bg=C["bg"], wraplength=630).pack(anchor=tk.W, padx=20, pady=(16, 2))
        if tagline:
            tk.Label(content, text=f"«{tagline}»", font=("Segoe UI", 10, "italic"),
                    fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20)
        tk.Label(content, text=f"{year}  •  ⭐ {rating:.1f}/10  •  {runtime} min  •  {genres}",
                font=("Segoe UI", 10), fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20, pady=(4, 0))

        tk.Label(content, text="\nSinopsis", font=("Segoe UI", 12, "bold"), fg=C["accent"],
                bg=C["bg"]).pack(anchor=tk.W, padx=20)
        tk.Label(content, text=overview, font=("Segoe UI", 10), fg=C["text"],
                bg=C["bg"], wraplength=630, justify="left").pack(
            anchor=tk.W, padx=20, pady=(4, 10))

        cast = credits.get("cast", [])[:8]
        if cast:
            tk.Label(content, text="Elenco", font=("Segoe UI", 12, "bold"), fg=C["accent"],
                    bg=C["bg"]).pack(anchor=tk.W, padx=20)
            for c in cast:
                tk.Label(content, text=f"  {c['name']} como {c.get('character', '?')}",
                        font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"]).pack(
                    anchor=tk.W, padx=20)

        if budget or revenue:
            info = []
            if budget: info.append(f"💰 Presupuesto: ${budget:,}")
            if revenue: info.append(f"📈 Recaudación: ${revenue:,}")
            tk.Label(content, text="\n" + " | ".join(info), font=("Segoe UI", 9),
                    fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20)

        trailers = [v for v in videos.get("results", [])
                    if v.get("type") == "Trailer" and v.get("site") == "YouTube"]
        if trailers:
            tk.Label(content, text="\nTrailer", font=("Segoe UI", 12, "bold"),
                    fg=C["accent"], bg=C["bg"]).pack(anchor=tk.W, padx=20)
            tk.Button(content, text=f"▶ Ver Trailer en YouTube",
                     command=lambda: webbrowser.open(f"https://www.youtube.com/watch?v={trailers[0]['key']}"),
                     font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                     relief=tk.FLAT, padx=16, pady=6, cursor="hand2").pack(
                anchor=tk.W, padx=20, pady=4)


def main():
    root = tk.Tk()
    NexusMovies(root)
    root.mainloop()


if __name__ == "__main__":
    main()
