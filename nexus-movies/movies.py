"""
NEXUS MOVIES v1.0 — Movie Browser & Discovery
Uses TMDB API (free tier). Netflix-style dark UI.
Browse trending, top rated, upcoming movies. Search, favorites, cast, trailers.
"""
import os, sys, json, urllib.request, urllib.parse, urllib.error, ssl, threading, webbrowser
from datetime import datetime
from pathlib import Path
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# TMDB API config — free dev key
API_KEY = "2dca580c2a14b55200e784d157207b4d"
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_SMALL = "https://image.tmdb.org/t/p/w200"
YOUTUBE_BASE = "https://www.youtube.com/watch?v="

C = {
    "bg": "#0a0a0f", "bg2": "#14141f", "bg3": "#0d0d18",
    "border": "#1e1e35", "text": "#e0e0e0", "dim": "#555568",
    "accent": "#e50914", "accent2": "#ff4757",
    "gold": "#f5c518", "green": "#46d369",
    "card": "#181825", "card_hover": "#1e1e30",
}

DATA_DIR = Path.home() / "Documents" / "NexusMovies"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FAVS_FILE = DATA_DIR / "favorites.json"
CACHE_FILE = DATA_DIR / "cache.json"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def api_get(endpoint, params=None):
    if params is None: params = {}
    params["api_key"] = API_KEY
    params["language"] = "es-MX"
    url = f"{BASE_URL}{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexusMovies/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"API error: {e}")
        return {}


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

        self._build()
        self._load_trending()

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
        tk.Label(hdr, text="v1.0  |  Movie Browser", font=("Segoe UI", 8),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Search bar
        search_f = tk.Frame(hdr, bg=C["bg"])
        search_f.pack(side=tk.RIGHT)
        self.search_e = tk.Entry(search_f, font=("Segoe UI", 10), bg=C["bg3"], fg=C["text"],
                                 insertbackground=C["accent"], relief=tk.FLAT, width=22)
        self.search_e.pack(side=tk.LEFT, ipady=4)
        self.search_e.bind("<Return>", lambda e: self._search())
        self.search_e.insert(0, "")
        tk.Button(search_f, text="🔍", command=self._search, font=("Segoe UI", 10),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=10, cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Category tabs
        cat_f = tk.Frame(self.root, bg=C["bg"])
        cat_f.pack(fill=tk.X, padx=16, pady=(6, 0))
        categories = [
            ("🔥 Trending", "trending", "/trending/movie/week"),
            ("⭐ Top Rated", "top", "/movie/top_rated"),
            ("🆕 Upcoming", "upcoming", "/movie/upcoming"),
            ("🎬 Now Playing", "now", "/movie/now_playing"),
            ("❤️ Favorites", "favs", None),
        ]
        self.cat_btns = {}
        for text, mode, endpoint in categories:
            btn = tk.Button(cat_f, text=text, command=lambda m=mode, e=endpoint: self._switch_mode(m, e),
                           font=("Segoe UI", 9), bg=C["bg2"], fg=C["dim"], relief=tk.FLAT,
                           padx=12, pady=5, cursor="hand2", activebackground=C["card"],
                           activeforeground=C["text"])
            btn.pack(side=tk.LEFT, padx=1)
            self.cat_btns[mode] = btn

        # Genre filter
        genre_f = tk.Frame(self.root, bg=C["bg"])
        genre_f.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.genre_var = tk.StringVar(value="All")
        tk.Label(genre_f, text="Género:", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT)
        self.genre_cb = ttk.Combobox(genre_f, textvariable=self.genre_var, state="readonly",
                                     font=("Segoe UI", 8), width=14)
        self.genre_cb.pack(side=tk.LEFT, padx=4)
        self.genre_cb.bind("<<ComboboxSelected>>", lambda e: self._filter_genre())
        self._load_genres()

        # Movie grid
        self.grid_frame = tk.Frame(self.root, bg=C["bg"])
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))

        # Canvas + scroll
        self.canvas = tk.Canvas(self.grid_frame, bg=C["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.grid_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=C["bg"])

        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 60), "units"))
        self.canvas.bind("<Configure>", lambda e: self._resize_grid(e.width))

        # Status
        self.status_lbl = tk.Label(self.root, text="Loading...", font=("Segoe UI", 8),
                                   fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

    def _resize_grid(self, width):
        self.root.after(100, lambda: self._render_grid())

    def _load_genres(self):
        data = api_get("/genre/movie/list")
        genres = data.get("genres", [])
        self.genres = {g["name"]: g["id"] for g in genres}
        self.genre_cb["values"] = ["All"] + sorted(self.genres.keys())
        self.genre_cb.set("All")

    def _switch_mode(self, mode, endpoint):
        self.current_mode = mode
        self.current_page = 1
        self.movies = []
        self.genre_var.set("All")

        for m, btn in self.cat_btns.items():
            btn.config(bg=C["bg2"], fg=C["dim"])
        self.cat_btns[mode].config(bg=C["accent"], fg="#fff")

        if mode == "favs":
            self.movies = load_favs()
            self._render_grid()
            self.status_lbl.config(text=f"❤️ {len(self.movies)} favorites")
        else:
            self.status_lbl.config(text="Loading...")
            self._endpoint = endpoint
            threading.Thread(target=self._fetch_movies, daemon=True).start()

    def _load_trending(self):
        self.current_mode = "trending"
        self._endpoint = "/trending/movie/week"
        self.cat_btns["trending"].config(bg=C["accent"], fg="#fff")
        threading.Thread(target=self._fetch_movies, daemon=True).start()

    def _fetch_movies(self):
        data = api_get(self._endpoint, {"page": self.current_page})
        new_movies = data.get("results", [])
        if self.current_page == 1:
            self.movies = new_movies
        else:
            self.movies.extend(new_movies)
        self.root.after(0, self._render_grid)
        self.root.after(0, lambda: self.status_lbl.config(
            text=f"{len(self.movies)} movies loaded"))

    def _search(self):
        query = self.search_e.get().strip()
        if not query: return
        self.current_mode = "search"
        self.status_lbl.config(text=f"🔍 Searching: {query}...")
        self.movies = []
        for m, btn in self.cat_btns.items():
            btn.config(bg=C["bg2"], fg=C["dim"])

        def _run():
            data = api_get("/search/movie", {"query": query})
            self.movies = data.get("results", [])
            self.root.after(0, self._render_grid)
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"🔍 {len(self.movies)} results for '{query}'"))

        threading.Thread(target=_run, daemon=True).start()

    def _filter_genre(self):
        genre_name = self.genre_var.get()
        if genre_name == "All":
            self.current_genre = None
        else:
            self.current_genre = self.genres.get(genre_name)

        if self.current_mode == "favs":
            return

        self.movies = []
        self.current_page = 1

        def _run():
            data = api_get("/discover/movie", {
                "with_genres": str(self.current_genre) if self.current_genre else None,
                "sort_by": "popularity.desc",
                "page": self.current_page
            })
            self.movies = data.get("results", [])
            self.root.after(0, self._render_grid)
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"{len(self.movies)} movies in genre"))

        threading.Thread(target=_run, daemon=True).start()

    def _render_grid(self):
        for widget in self.scroll_content.winfo_children():
            widget.destroy()
        self.photo_refs.clear()

        canvas_w = self.canvas.winfo_width() or 900
        cols = max(2, canvas_w // 170)
        pad = 8

        filtered = self.movies[:100]  # Limit display

        for i, movie in enumerate(filtered):
            if not movie.get("poster_path"): continue

            row = i // cols
            col = i % cols
            x = col * (160 + pad) + pad
            y = row * (290 + pad) + pad

            card = tk.Frame(self.scroll_content, bg=C["card"],
                           highlightbackground=C["border"], highlightthickness=1,
                           cursor="hand2")
            card.place(x=x, y=y, width=160, height=290)

            # Poster
            poster_url = f"{IMG_BASE}{movie['poster_path']}"
            poster_frame = tk.Frame(card, bg=C["card"])
            poster_frame.pack(fill=tk.X)

            placeholder = tk.Label(poster_frame, text="🎬", font=("Segoe UI", 30),
                                  bg=C["bg3"], fg=C["dim"], height=6)
            placeholder.pack(fill=tk.X)

            # Load poster asynchronously
            threading.Thread(target=self._load_poster,
                           args=(poster_url, placeholder, card, movie),
                           daemon=True).start()

            # Rating
            rating = movie.get("vote_average", 0)
            rating_str = f"⭐ {rating:.1f}" if rating else "—"
            tk.Label(card, text=rating_str, font=("Segoe UI", 8, "bold"),
                    fg=C["gold"], bg=C["card"]).pack(pady=(2, 0))

            # Title
            title = movie.get("title", "Unknown")[:25]
            tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), fg=C["text"],
                    bg=C["card"], wraplength=150, justify="center").pack(pady=(0, 2))

            # Year
            year = (movie.get("release_date", "") or "")[:4] or "—"
            tk.Label(card, text=year, font=("Segoe UI", 8), fg=C["dim"],
                    bg=C["card"]).pack()

            # Heart button
            is_fav = any(f.get("id") == movie.get("id") for f in self.favorites)
            fav_btn = tk.Label(card, text="❤️" if is_fav else "🤍",
                              font=("Segoe UI", 11), bg=C["card"], fg=C["accent"] if is_fav else C["dim"],
                              cursor="hand2")
            fav_btn.pack(pady=(2, 0))
            fav_btn.bind("<Button-1>", lambda e, m=movie: self._toggle_fav(m))

            # Click on poster for details
            placeholder.bind("<Button-1>", lambda e, m=movie: self._show_detail(m))
            card.bind("<Button-1>", lambda e, m=movie: self._show_detail(m))

        # Load more button
        if self.current_mode not in ("favs", "search") and len(self.movies) >= 20:
            y_pos = ((len(filtered) - 1) // cols + 1) * (290 + pad) + pad
            load_btn = tk.Button(self.scroll_content, text="▼ Load More", command=self._load_more,
                                font=("Segoe UI", 10, "bold"), bg=C["bg2"], fg=C["text"],
                                relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
            load_btn.place(x=pad, y=y_pos, width=canvas_w - 2 * pad)

    def _load_poster(self, url, placeholder, card, movie):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NexusMovies/1.0"})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                data = resp.read()
            try:
                from PIL import Image, ImageTk
                img = Image.open(BytesIO(data))
                img = img.resize((160, 240), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_refs.append(photo)
                placeholder.config(image=photo, text="", height=240)
                placeholder.image = photo
            except ImportError:
                placeholder.config(text="🎬", font=("Segoe UI", 25))
        except:
            pass

    def _load_more(self):
        self.current_page += 1
        self.status_lbl.config(text=f"Loading page {self.current_page}...")
        threading.Thread(target=self._fetch_movies, daemon=True).start()

    def _toggle_fav(self, movie):
        idx = next((i for i, f in enumerate(self.favorites) if f.get("id") == movie.get("id")), -1)
        if idx >= 0:
            self.favorites.pop(idx)
        else:
            self.favorites.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
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

        # Fetch full details
        self.status_lbl.config(text="Loading details...")

        def _run():
            details = api_get(f"/movie/{mid}")
            credits = api_get(f"/movie/{mid}/credits")
            videos = api_get(f"/movie/{mid}/videos")
            self.root.after(0, lambda: self._open_detail_window(movie, details, credits, videos))

        threading.Thread(target=_run, daemon=True).start()

    def _open_detail_window(self, movie, details, credits, videos):
        win = tk.Toplevel(self.root)
        win.title(movie.get("title", "Movie"))
        win.geometry("700x600")
        win.configure(bg=C["bg"])
        win.minsize(500, 400)

        # Center
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 700) // 2
        y = (win.winfo_screenheight() - 600) // 2
        win.geometry(f"+{x}+{y}")

        # Scrollable content
        canvas = tk.Canvas(win, bg=C["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=C["bg"])

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        title = details.get("title", movie.get("title", "Unknown"))
        year = (details.get("release_date", "") or "")[:4]
        rating = details.get("vote_average", 0)
        runtime = details.get("runtime", 0)
        genres = ", ".join(g["name"] for g in details.get("genres", []))
        overview = details.get("overview", "No description available.")
        budget = details.get("budget", 0)
        revenue = details.get("revenue", 0)

        # Header
        tk.Label(content, text=title, font=("Segoe UI", 18, "bold"), fg=C["text"],
                bg=C["bg"], wraplength=650).pack(anchor=tk.W, padx=20, pady=(16, 4))
        tk.Label(content, text=f"{year}  •  ⭐ {rating:.1f}/10  •  {runtime} min  •  {genres}",
                font=("Segoe UI", 10), fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20)

        # Overview
        tk.Label(content, text="\nSinopsis", font=("Segoe UI", 12, "bold"), fg=C["accent"],
                bg=C["bg"]).pack(anchor=tk.W, padx=20)
        tk.Label(content, text=overview, font=("Segoe UI", 10), fg=C["text"],
                bg=C["bg"], wraplength=650, justify="left").pack(anchor=tk.W, padx=20, pady=(4, 10))

        # Cast
        cast = credits.get("cast", [])[:8]
        if cast:
            tk.Label(content, text="Elenco", font=("Segoe UI", 12, "bold"), fg=C["accent"],
                    bg=C["bg"]).pack(anchor=tk.W, padx=20)
            cast_text = "  •  ".join(f"{c['name']} ({c.get('character', '?')})" for c in cast)
            tk.Label(content, text=cast_text, font=("Segoe UI", 9), fg=C["dim"],
                    bg=C["bg"], wraplength=650, justify="left").pack(
                anchor=tk.W, padx=20, pady=(4, 10))

        # Additional info
        if budget or revenue:
            info_text = []
            if budget: info_text.append(f"Presupuesto: ${budget:,}")
            if revenue: info_text.append(f"Recaudación: ${revenue:,}")
            tk.Label(content, text=" | ".join(info_text), font=("Segoe UI", 9),
                    fg=C["dim"], bg=C["bg"]).pack(anchor=tk.W, padx=20, pady=(0, 5))

        # Trailer
        trailers = [v for v in videos.get("results", []) if v.get("type") == "Trailer" and v.get("site") == "YouTube"]
        if trailers:
            trailer = trailers[0]
            tk.Label(content, text="\nTrailer", font=("Segoe UI", 12, "bold"), fg=C["accent"],
                    bg=C["bg"]).pack(anchor=tk.W, padx=20)
            yt_url = f"{YOUTUBE_BASE}{trailer['key']}"
            tk.Button(content, text="▶ Watch Trailer on YouTube", command=lambda: webbrowser.open(yt_url),
                     font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff", relief=tk.FLAT,
                     padx=16, pady=6, cursor="hand2").pack(anchor=tk.W, padx=20, pady=4)


def main():
    root = tk.Tk()
    NexusMovies(root)
    root.mainloop()


if __name__ == "__main__":
    main()
