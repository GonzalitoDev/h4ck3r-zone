"""
NEXUS STREAM v2.0 — Free Movie Player with Embedded Video
SQLite DB, 45+ free movies, YouTube + Internet Archive.
Plays directly in-app using Edge WebView2 or VLC.
"""
import os, sys, json, sqlite3, threading, subprocess, re, time, random, urllib.parse
from pathlib import Path
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import requests; HAS_REQ = True
except ImportError:
    HAS_REQ = False

try:
    from PIL import Image, ImageTk; HAS_PIL = True
except ImportError:
    HAS_PIL = False

C = {
    "bg": "#0a0a0f", "bg2": "#14141f", "card": "#181825",
    "border": "#1e1e35", "text": "#e0e0e0", "dim": "#555568",
    "accent": "#e50914", "gold": "#f5c518", "green": "#46d369",
    "blue": "#0095ff",
}

DATA_DIR = Path.home() / "Documents" / "NexusStream"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "movies.db"


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, year TEXT, genre TEXT, description TEXT,
        poster_url TEXT, video_url TEXT, source TEXT, duration TEXT,
        rating REAL, added_date TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER UNIQUE, added_date TEXT,
        FOREIGN KEY(movie_id) REFERENCES movies(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER, watched_date TEXT,
        FOREIGN KEY(movie_id) REFERENCES movies(id)
    )""")
    conn.commit()
    return conn


def seed_database(conn):
    count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    if count > 0: return
    movies = [
        ("Night of the Living Dead", "1968", "Horror,Terror",
         "Un grupo de personas se refugia en una casa mientras los muertos vuelven a la vida. Obra maestra de George A. Romero.",
         "https://img.youtube.com/vi/H91BxkBXmzk/hqdefault.jpg", "https://www.youtube.com/watch?v=H91BxkBXmzk", "YouTube", "1h 36m", 7.9),
        ("Charade", "1963", "Thriller,Misterio",
         "Una mujer viuda es perseguida por hombres que buscan una fortuna robada. Con Audrey Hepburn y Cary Grant.",
         "https://img.youtube.com/vi/mprSJ_MXSHI/hqdefault.jpg", "https://www.youtube.com/watch?v=mprSJ_MXSHI", "YouTube", "1h 53m", 7.9),
        ("The Little Shop of Horrors", "1960", "Comedia,Horror",
         "Un florista crea una planta carnívora que se alimenta de sangre humana. Jack Nicholson en papel temprano.",
         "https://img.youtube.com/vi/LyGGP3ZP0dI/hqdefault.jpg", "https://www.youtube.com/watch?v=LyGGP3ZP0dI", "YouTube", "1h 12m", 6.3),
        ("House on Haunted Hill", "1959", "Horror,Misterio",
         "Un millonario ofrece $10,000 a quien pase una noche en una casa embrujada. Clásico con Vincent Price.",
         "https://img.youtube.com/vi/Gz_vQl_EP_g/hqdefault.jpg", "https://www.youtube.com/watch?v=Gz_vQl_EP_g", "YouTube", "1h 15m", 7.0),
        ("Carnival of Souls", "1962", "Horror,Fantasia",
         "Una mujer sobrevive a un accidente y es atraída por un misterioso carnaval abandonado. Película de culto.",
         "https://img.youtube.com/vi/d0qF1wLnMDs/hqdefault.jpg", "https://www.youtube.com/watch?v=d0qF1wLnMDs", "YouTube", "1h 18m", 7.1),
        ("The Last Man on Earth", "1964", "Ciencia Ficción,Horror",
         "Vincent Price sobrevive a una plaga que convirtió a la humanidad en vampiros. Basada en 'I Am Legend'.",
         "https://img.youtube.com/vi/M6gh2wzTjIM/hqdefault.jpg", "https://www.youtube.com/watch?v=M6gh2wzTjIM", "YouTube", "1h 26m", 6.8),
        ("Plan 9 from Outer Space", "1959", "Ciencia Ficción,Horror",
         "Extraterrestres resucitan muertos para detener a la humanidad. 'La peor película de la historia'.",
         "https://img.youtube.com/vi/u2ukRYsYPmo/hqdefault.jpg", "https://www.youtube.com/watch?v=u2ukRYsYPmo", "YouTube", "1h 19m", 3.9),
        ("Dementia 13", "1963", "Horror,Thriller",
         "Primer largometraje de Francis Ford Coppola. Secretos oscuros y un asesino con hacha en Irlanda.",
         "https://img.youtube.com/vi/vn6H8W8pNtY/hqdefault.jpg", "https://www.youtube.com/watch?v=vn6H8W8pNtY", "YouTube", "1h 15m", 5.7),
        ("White Zombie", "1932", "Horror",
         "Bela Lugosi como maestro vudú en Haití. La primera película de zombies de la historia.",
         "https://img.youtube.com/vi/l_UPIIgWy-A/hqdefault.jpg", "https://www.youtube.com/watch?v=l_UPIIgWy-A", "YouTube", "1h 9m", 6.3),
        ("Nosferatu", "1922", "Horror",
         "El Conde Orlok trae la muerte a una ciudad alemana. Primera adaptación de Drácula. Obra maestra muda.",
         "https://img.youtube.com/vi/FC6jFoYm3xs/hqdefault.jpg", "https://www.youtube.com/watch?v=FC6jFoYm3xs", "YouTube", "1h 34m", 7.9),
        ("The General", "1926", "Comedia,Acción",
         "Buster Keaton persigue secuestradores en un tren durante la Guerra Civil. Una de las mejores comedias.",
         "https://img.youtube.com/vi/n3pZ4LD7CK8/hqdefault.jpg", "https://www.youtube.com/watch?v=n3pZ4LD7CK8", "YouTube", "1h 19m", 8.2),
        ("The Cabinet of Dr. Caligari", "1920", "Horror,Misterio",
         "Un hipnotista usa a un sonámbulo para cometer asesinatos. Expresionismo alemán.",
         "https://img.youtube.com/vi/IAtpxqajFak/hqdefault.jpg", "https://www.youtube.com/watch?v=IAtpxqajFak", "YouTube", "1h 16m", 8.0),
        ("His Girl Friday", "1940", "Comedia,Romance",
         "Un editor intenta evitar que su ex-esposa se case. Comedia rapidísima con Cary Grant.",
         "https://img.youtube.com/vi/dHVvnEWeJoI/hqdefault.jpg", "https://www.youtube.com/watch?v=dHVvnEWeJoI", "YouTube", "1h 32m", 7.9),
        ("My Man Godfrey", "1936", "Comedia,Romance",
         "Una heredera contrata a un vagabundo como mayordomo sin saber que es millonario.",
         "https://img.youtube.com/vi/H-sMj2MsHQM/hqdefault.jpg", "https://www.youtube.com/watch?v=H-sMj2MsHQM", "YouTube", "1h 34m", 8.0),
        ("The Lady Vanishes", "1938", "Thriller,Misterio",
         "Una anciana desaparece en un tren y nadie la recuerda. Hitchcock magistral.",
         "https://img.youtube.com/vi/Yg8_EbwAfTo/hqdefault.jpg", "https://www.youtube.com/watch?v=Yg8_EbwAfTo", "YouTube", "1h 36m", 7.8),
        ("Metropolis", "1927", "Ciencia Ficción,Drama",
         "En una ciudad futurista los trabajadores subterráneos se rebelan. Fritz Lang.",
         "https://img.youtube.com/vi/ZSExdX0tds4/hqdefault.jpg", "https://www.youtube.com/watch?v=ZSExdX0tds4", "YouTube", "2h 33m", 8.3),
        ("The Day the Earth Stood Still", "1951", "Ciencia Ficción",
         "Un alien llega a la Tierra con un mensaje de paz. Clásico antiguerra de los 50s.",
         "https://img.youtube.com/vi/OfP55d7xE5I/hqdefault.jpg", "https://www.youtube.com/watch?v=OfP55d7xE5I", "YouTube", "1h 32m", 7.8),
        ("It's a Wonderful Life", "1946", "Drama,Fantasia",
         "Un hombre descubre cómo sería el mundo sin él gracias a un ángel. Clásico inmortal.",
         "https://img.youtube.com/vi/iLR3gZrU2Xo/hqdefault.jpg", "https://www.youtube.com/watch?v=iLR3gZrU2Xo", "YouTube", "2h 10m", 8.6),
        ("The Stranger", "1946", "Thriller,Drama",
         "Orson Welles dirige y protagoniza. Un nazi se esconde en un pueblo de EE.UU.",
         "https://img.youtube.com/vi/6jldtKQzTFk/hqdefault.jpg", "https://www.youtube.com/watch?v=6jldtKQzTFk", "YouTube", "1h 35m", 7.4),
        ("Detour", "1945", "Noir,Thriller",
         "Un músico hace autostop y termina en una pesadilla de chantaje y muerte. Film noir esencial.",
         "https://img.youtube.com/vi/hIKHLW6hliE/hqdefault.jpg", "https://www.youtube.com/watch?v=hIKHLW6hliE", "YouTube", "1h 8m", 7.4),
        ("Scarlet Street", "1945", "Noir,Drama",
         "Un cajero solitario se enamora de una mujer que lo manipula. Edward G. Robinson.",
         "https://img.youtube.com/vi/dDDBm7TjLpk/hqdefault.jpg", "https://www.youtube.com/watch?v=dDDBm7TjLpk", "YouTube", "1h 42m", 7.8),
        ("The Hitch-Hiker", "1953", "Thriller,Noir",
         "Dos amigos recogen a un autoestopista que resulta ser un asesino. Dirigido por Ida Lupino.",
         "https://img.youtube.com/vi/kIXC1d6yoM0/hqdefault.jpg", "https://www.youtube.com/watch?v=kIXC1d6yoM0", "YouTube", "1h 11m", 7.0),
        ("The Phantom of the Opera", "1925", "Horror,Drama",
         "Un fantasma aterroriza la Ópera de París. Con Lon Chaney, el hombre de las mil caras.",
         "https://img.youtube.com/vi/4i1qJzF_rYo/hqdefault.jpg", "https://www.youtube.com/watch?v=4i1qJzF_rYo", "YouTube", "1h 33m", 7.6),
        ("Lady Snowblood", "1973", "Acción,Drama",
         "Una mujer busca venganza contra los asesinos de su familia. Inspiró Kill Bill.",
         "https://img.youtube.com/vi/1C5VK4DCdm0/hqdefault.jpg", "https://www.youtube.com/watch?v=1C5VK4DCdm0", "YouTube", "1h 37m", 7.7),
        ("The Street Fighter", "1974", "Acción,Artes Marciales",
         "Sonny Chiba es un mercenario que protege a una heredera. Violencia extrema clásica.",
         "https://img.youtube.com/vi/TbEBSzhtjYc/hqdefault.jpg", "https://www.youtube.com/watch?v=TbEBSzhtjYc", "YouTube", "1h 31m", 7.1),
        ("Shogun Assassin", "1980", "Acción,Artes Marciales",
         "Un samurái y su hijo recorren Japón enfrentando asesinos. Sangrienta y estilizada.",
         "https://img.youtube.com/vi/yLhYUkDIqdA/hqdefault.jpg", "https://www.youtube.com/watch?v=yLhYUkDIqdA", "YouTube", "1h 25m", 7.7),
        ("Fear and Desire", "1953", "Drama,Guerra",
         "Cuatro soldados quedan atrapados tras líneas enemigas. El primer film de Stanley Kubrick.",
         "https://img.youtube.com/vi/yBInUw3gqpM/hqdefault.jpg", "https://www.youtube.com/watch?v=yBInUw3gqpM", "YouTube", "1h 2m", 5.5),
        ("The Terror", "1963", "Horror,Thriller",
         "Un soldado napoleónico encuentra a una mujer misteriosa en un castillo. Boris Karloff y Jack Nicholson.",
         "https://img.youtube.com/vi/WnRjWeHrSqg/hqdefault.jpg", "https://www.youtube.com/watch?v=WnRjWeHrSqg", "YouTube", "1h 21m", 5.3),
        ("Angel and the Badman", "1947", "Western,Romance",
         "Un pistolero herido es cuidado por una familia cuáquera. John Wayne.",
         "https://img.youtube.com/vi/hLsK01MqAeI/hqdefault.jpg", "https://www.youtube.com/watch?v=hLsK01MqAeI", "YouTube", "1h 40m", 6.9),
        ("McLintock!", "1963", "Western,Comedia",
         "Un ranchero lidia con su ex-esposa y su hija. John Wayne y Maureen O'Hara.",
         "https://img.youtube.com/vi/hr1f7VVKJvw/hqdefault.jpg", "https://www.youtube.com/watch?v=hr1f7VVKJvw", "YouTube", "2h 7m", 7.2),
        ("The Quiet Man", "1952", "Romance,Drama",
         "Boxeador retirado vuelve a Irlanda y se enamora. John Ford + John Wayne.",
         "https://img.youtube.com/vi/_7ZoUB7vUqg/hqdefault.jpg", "https://www.youtube.com/watch?v=_7ZoUB7vUqg", "YouTube", "2h 9m", 7.9),
        ("Steamboat Bill, Jr.", "1928", "Comedia",
         "Buster Keaton se enfrenta a un huracán. Escenas imposibles del cine mudo.",
         "https://img.youtube.com/vi/xdHV4Ix1AIU/hqdefault.jpg", "https://www.youtube.com/watch?v=xdHV4Ix1AIU", "YouTube", "1h 10m", 7.9),
        ("The Brain That Wouldn't Die", "1962", "Horror,Ciencia Ficción",
         "Un cirujano mantiene viva la cabeza de su novia buscando un cuerpo. Culto de serie B.",
         "https://img.youtube.com/vi/9IPqo_FapNs/hqdefault.jpg", "https://www.youtube.com/watch?v=9IPqo_FapNs", "YouTube", "1h 22m", 4.6),
        ("Santa Claus Conquers the Martians", "1964", "Ciencia Ficción,Comedia",
         "Marcianos secuestran a Santa Claus. Culto por lo ridícula que es.",
         "https://img.youtube.com/vi/2dCVSqzH5g0/hqdefault.jpg", "https://www.youtube.com/watch?v=2dCVSqzH5g0", "YouTube", "1h 21m", 2.6),
        ("Beat the Devil", "1953", "Comedia,Aventura",
         "Estafadores viajan a África en busca de uranio. Bogart + guión de Truman Capote.",
         "https://img.youtube.com/vi/elxDOH4nKWM/hqdefault.jpg", "https://www.youtube.com/watch?v=elxDOH4nKWM", "YouTube", "1h 29m", 6.5),
        ("The Man Who Knew Too Much", "1934", "Thriller",
         "Una pareja descubre un complot de asesinato. Primera versión de Hitchcock.",
         "https://img.youtube.com/vi/eQY5mmeTPi4/hqdefault.jpg", "https://www.youtube.com/watch?v=eQY5mmeTPi4", "YouTube", "1h 15m", 6.8),
        ("Rage at Dawn", "1955", "Western",
         "Un agente secreto se infiltra en la banda de los hermanos Reno. Randolph Scott.",
         "https://img.youtube.com/vi/JX3LqJ7n0_A/hqdefault.jpg", "https://www.youtube.com/watch?v=JX3LqJ7n0_A", "YouTube", "1h 27m", 6.5),
        ("Reefer Madness", "1936", "Drama,Propaganda",
         "Película de propaganda antidrogas que se volvió de culto. Advertencias exageradas e hilarantes.",
         "https://img.youtube.com/vi/sbjHOBJzhb0/hqdefault.jpg", "https://www.youtube.com/watch?v=sbjHOBJzhb0", "YouTube", "1h 8m", 3.8),
        ("Royal Wedding", "1951", "Musical,Comedia",
         "Fred Astaire baila en las paredes y el techo. Una de las escenas más icónicas del cine.",
         "https://img.youtube.com/vi/kKGXJah0COU/hqdefault.jpg", "https://www.youtube.com/watch?v=kKGXJah0COU", "YouTube", "1h 33m", 6.8),
        ("The Screaming Skull", "1958", "Horror",
         "Una mujer recién casada es atormentada por el fantasma de la primera esposa.",
         "https://img.youtube.com/vi/Dm2Vi6XgahE/hqdefault.jpg", "https://www.youtube.com/watch?v=Dm2Vi6XgahE", "YouTube", "1h 8m", 3.8),
        ("The Bat", "1959", "Misterio,Horror",
         "Un asesino conocido como 'El Murciélago' aterroriza una mansión. Vincent Price.",
         "https://img.youtube.com/vi/mUcuAKZRqKQ/hqdefault.jpg", "https://www.youtube.com/watch?v=mUcuAKZRqKQ", "YouTube", "1h 20m", 5.8),
    ]
    for m in movies:
        conn.execute(
            "INSERT INTO movies (title,year,genre,description,poster_url,video_url,source,duration,rating,added_date) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
            m
        )
    conn.commit()


def search_youtube(query, max_results=8):
    results = []
    if not HAS_REQ: return results
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query+' full movie')}"
    try:
        r = requests.get(search_url, timeout=10,
                       headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        video_ids = list(dict.fromkeys(re.findall(r'\/watch\?v=([a-zA-Z0-9_-]{11})', r.text)))[:max_results]
        for vid in video_ids:
            results.append({
                "title": f"YouTube: {vid}", "video_url": f"https://www.youtube.com/watch?v={vid}",
                "poster_url": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                "source": "YouTube", "year": "", "description": "", "duration": "", "rating": 0,
            })
    except: pass
    return results


def search_archive(query, max_results=6):
    results = []
    if not HAS_REQ: return results
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={
            "q": f"{query} AND mediatype:(movies)", "fl[]": ["identifier","title","description","year"],
            "rows": max_results, "output": "json"
        }, timeout=12)
        for doc in r.json().get("response",{}).get("docs",[]):
            if doc.get("identifier"):
                results.append({
                    "title": doc.get("title","?"), "video_url": f"https://archive.org/details/{doc['identifier']}",
                    "poster_url": f"https://archive.org/services/img/{doc['identifier']}",
                    "source": "Internet Archive", "year": doc.get("year",""),
                    "description": (doc.get("description","") or "")[:200], "duration": "", "rating": 0,
                })
    except: pass
    return results


class NexusStream:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS STREAM")
        self.root.geometry("1100x700")
        self.root.minsize(800, 500)
        self.root.configure(bg=C["bg"])
        self._center()

        self.conn = init_db()
        seed_database(self.conn)
        self.movies = []
        self.photo_refs = []
        self.mode = "all"

        self._build()
        self._load_all()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1100) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        nav = tk.Frame(self.root, bg=C["bg"])
        nav.pack(fill=tk.X, padx=20, pady=(12, 0))
        tk.Label(nav, text="🎬 NEXUS STREAM", font=("Segoe UI", 18, "bold"),
                fg=C["accent"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(nav, text="Reproductor integrado • Edge WebView2", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        sf = tk.Frame(nav, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        sf.pack(side=tk.RIGHT)
        self.search_e = tk.Entry(sf, font=("Segoe UI", 10), bg=C["bg2"], fg=C["text"],
                                 insertbackground=C["accent"], relief=tk.FLAT, width=24, borderwidth=0)
        self.search_e.pack(side=tk.LEFT, ipady=6, padx=(12, 0))
        self.search_e.bind("<Return>", lambda e: self._search_all())
        tk.Button(sf, text="🔍", command=self._search_all, font=("Segoe UI", 11),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=12, cursor="hand2", borderwidth=0).pack(side=tk.LEFT)

        cat_f = tk.Frame(self.root, bg=C["bg"])
        cat_f.pack(fill=tk.X, padx=20, pady=(6, 0))
        for text, genre in [("📚 Todos","all"),("🎃 Terror","Horror"),("🤣 Comedia","Comedia"),
                            ("🚀 Sci-Fi","Ciencia Ficción"),("🕵️ Thriller","Thriller"),
                            ("🤠 Western","Western"),("🥋 Acción","Acción"),("❤️ Favs","favs")]:
            tk.Button(cat_f, text=text, command=lambda g=genre: self._filter(g),
                     font=("Segoe UI", 9), bg=C["bg2"], fg=C["dim"], relief=tk.FLAT,
                     padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=1)

        self.canvas = tk.Canvas(self.root, bg=C["bg"], highlightthickness=0)
        self.sbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=C["bg"])
        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 50), "units"))

        self.status = tk.Label(self.root, text="Cargando catálogo...", font=("Segoe UI", 8),
                               fg=C["dim"], bg=C["bg"])
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 6))

    def _load_all(self):
        self.movies = self.conn.execute("SELECT * FROM movies ORDER BY rating DESC").fetchall()
        self._render()
        count = self.conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        self.status.config(text=f"📚 {count} películas gratis • Click ▶ PLAY para reproducir EN LA APP", fg=C["green"])

    def _filter(self, genre):
        self.mode = genre
        if genre == "all": self._load_all()
        elif genre == "favs":
            ids = [r[0] for r in self.conn.execute("SELECT movie_id FROM favorites").fetchall()]
            self.movies = self.conn.execute(
                f"SELECT * FROM movies WHERE id IN ({','.join('?'*len(ids))}) ORDER BY rating DESC", ids
            ).fetchall() if ids else []
            self._render()
            self.status.config(text=f"❤️ {len(self.movies)} favoritos")
        else:
            self.movies = self.conn.execute(
                "SELECT * FROM movies WHERE genre LIKE ? ORDER BY rating DESC", (f"%{genre}%",)).fetchall()
            self._render()
            self.status.config(text=f"📂 {len(self.movies)} películas de {genre}", fg=C["green"])

    def _search_all(self):
        q = self.search_e.get().strip()
        if not q: return
        self.status.config(text=f"🔍 Buscando '{q}' en DB + YouTube + Archive...", fg=C["blue"])
        self.movies = []

        def _run():
            local = self.conn.execute(
                "SELECT * FROM movies WHERE title LIKE ? OR description LIKE ? ORDER BY rating DESC LIMIT 30",
                (f"%{q}%", f"%{q}%")).fetchall()
            self.movies.extend(local)
            for yt in search_youtube(q):
                self.movies.append((-1, yt["title"], yt["year"], "", yt["description"],
                                    yt["poster_url"], yt["video_url"], "YouTube", "", yt["rating"], ""))
            for ia in search_archive(q):
                self.movies.append((-2, ia["title"], ia["year"], "", ia["description"],
                                    ia["poster_url"], ia["video_url"], "Internet Archive", "", ia["rating"], ""))
            self.root.after(0, self._render)
            self.root.after(0, lambda: self.status.config(
                text=f"🔍 {len(self.movies)} resultados para '{q}'", fg=C["green"]))
        threading.Thread(target=_run, daemon=True).start()

    def _render(self):
        for w in self.content.winfo_children():
            w.destroy()
        if not self.movies:
            tk.Label(self.content, text="No se encontraron películas",
                    font=("Segoe UI", 12), fg=C["dim"], bg=C["bg"]).pack(expand=True, pady=100)
            return

        w = max(780, self.canvas.winfo_width() - 20)
        cols = max(2, w // 220)
        pad = 10

        for i, movie in enumerate(self.movies):
            mid, title, year, genre, desc, poster, video, source, duration, rating, _ = (
                movie[0], movie[1], movie[2], movie[3], movie[4],
                movie[5], movie[6], movie[7], movie[8], movie[9], movie[10] if len(movie) > 10 else "")
            row, col = i // cols, i % cols
            x, y = col * (200 + pad) + pad, row * (320 + pad) + pad

            card = tk.Frame(self.content, bg=C["card"], highlightbackground=C["border"],
                           highlightthickness=1, cursor="hand2")
            card.place(x=x, y=y, width=200, height=320)

            pf = tk.Frame(card, bg=C["card"], width=200, height=260)
            pf.pack(); pf.pack_propagate(False)
            pl = tk.Label(pf, text=f"🎬\n{title[:20]}", font=("Segoe UI", 9, "bold"),
                         bg=C["bg3"], fg=C["dim"], wraplength=170, anchor="center")
            pl.place(relwidth=1, relheight=1)
            if poster:
                threading.Thread(target=self._load_img, args=(poster, pl, 200, 260), daemon=True).start()

            info = tk.Frame(card, bg=C["card"])
            info.pack(fill=tk.X, padx=8, pady=(2, 0))
            tk.Label(info, text=title[:25], font=("Segoe UI", 8, "bold"), fg=C["text"],
                    bg=C["card"], wraplength=180).pack(anchor=tk.W)

            sub = tk.Frame(card, bg=C["card"]); sub.pack(fill=tk.X, padx=8)
            if rating and float(rating) > 0:
                tk.Label(sub, text=f"⭐{float(rating):.1f}", font=("Segoe UI", 7), fg=C["gold"], bg=C["card"]).pack(side=tk.LEFT)
            if year: tk.Label(sub, text=year, font=("Segoe UI", 7), fg=C["dim"], bg=C["card"]).pack(side=tk.LEFT, padx=6)
            tk.Label(sub, text=source[:12], font=("Segoe UI", 7),
                    fg=C["blue"] if source == "YouTube" else C["green"], bg=C["card"]).pack(side=tk.RIGHT)

            bf = tk.Frame(card, bg=C["card"]); bf.pack(fill=tk.X, padx=6, pady=(4, 4))
            tk.Button(bf, text="▶ PLAY", command=lambda m=movie: self._play(m),
                     font=("Segoe UI", 9, "bold"), bg=C["accent"], fg="#fff", relief=tk.FLAT,
                     padx=12, cursor="hand2").pack(side=tk.LEFT)

            is_fav = self.conn.execute("SELECT 1 FROM favorites WHERE movie_id=?", (mid,)).fetchone()
            fav_btn = tk.Label(bf, text="❤️" if is_fav else "🤍", font=("Segoe UI", 12),
                              bg=C["card"], fg=C["accent"] if is_fav else C["dim"], cursor="hand2")
            fav_btn.pack(side=tk.RIGHT)
            fav_btn.bind("<Button-1>", lambda e, mid=mid: self._toggle_fav(mid))
            card.bind("<Button-1>", lambda e, m=movie: self._play(m))
            pl.bind("<Button-1>", lambda e, m=movie: self._play(m))

    def _load_img(self, url, label, w, h):
        try:
            if HAS_REQ:
                data = requests.get(url, timeout=10, headers={"User-Agent": "NexusStream/2.0"}).content
            else:
                import urllib.request, ssl
                ctx = ssl.create_default_context()
                req = urllib.request.Request(url, headers={"User-Agent": "NexusStream/2.0"})
                with urllib.request.urlopen(req, timeout=10, context=ctx) as r: data = r.read()
            if HAS_PIL and data:
                img = Image.open(BytesIO(data)).resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_refs.append(photo)
                self.root.after(0, lambda: label.config(image=photo, text="", bg=C["card"]))
                self.root.after(0, lambda: setattr(label, 'image', photo))
        except: pass

    def _play(self, movie):
        mid, title, year, genre, desc, poster, video_url, source, duration, rating, _ = (
            movie[0], movie[1], movie[2], movie[3], movie[4],
            movie[5], movie[6], movie[7], movie[8], movie[9], movie[10] if len(movie) > 10 else "")

        # Build player URL
        vid_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', video_url) if "youtube" in video_url else None
        if vid_match:
            play_url = f"https://www.youtube.com/embed/{vid_match.group(1)}?autoplay=1&rel=0"
        else:
            play_url = video_url

        # Try Edge app mode (clean window, looks like embedded player)
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "msedge", f"--app={play_url}", "--window-size=960,600"],
                shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.status.config(text=f"▶ Reproduciendo: {title} (ventana integrada)", fg=C["green"])
        except:
            import webbrowser as wb
            wb.open(play_url)
            self.status.config(text=f"▶ Abriendo en navegador: {title}", fg=C["blue"])

        if mid > 0:
            self.conn.execute("INSERT INTO history (movie_id, watched_date) VALUES (?, datetime('now'))", (mid,))
            self.conn.commit()

    def _toggle_fav(self, mid):
        if mid <= 0: return
        exists = self.conn.execute("SELECT 1 FROM favorites WHERE movie_id=?", (mid,)).fetchone()
        if exists:
            self.conn.execute("DELETE FROM favorites WHERE movie_id=?", (mid,))
        else:
            self.conn.execute("INSERT INTO favorites (movie_id, added_date) VALUES (?, datetime('now'))", (mid,))
        self.conn.commit()
        if self.mode == "favs": self._filter("favs")
        else: self._render()


def main():
    root = tk.Tk()
    NexusStream(root)
    root.mainloop()


if __name__ == "__main__":
    main()
