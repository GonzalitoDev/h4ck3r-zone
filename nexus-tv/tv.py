"""
NEXUS TV v1.0 — Free TV Streaming
Curated free legal channels. Built-in player via Edge app mode.
No ads, no signup, 100% free.
"""
import os, sys, json, subprocess, threading, webbrowser, urllib.parse
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

C={"bg":"#0a0a10","bg2":"#121220","card":"#181830","border":"#1e1e40","text":"#d0d0e4","dim":"#484870","accent":"#e50914","accent2":"#ff4757","green":"#34d399","gold":"#fbbf24","blue":"#60a5fa","live":"#ff0000"}

DATA_DIR=Path.home()/"Documents"/"NexusTV"
DATA_DIR.mkdir(parents=True,exist_ok=True)
FAVS_FILE=DATA_DIR/"favorites.json"

CHANNELS = [
    # NEWS - using YouTube watch URLs (more reliable than embed)
    {"name":"France 24 English","url":"https://www.youtube.com/watch?v=igRL6eR5PvI","cat":"News","lang":"EN","desc":"24/7 international news (English)"},
    {"name":"DW News","url":"https://www.youtube.com/watch?v=b63V1msNNQM","cat":"News","lang":"EN","desc":"Deutsche Welle live news"},
    {"name":"Al Jazeera English","url":"https://www.youtube.com/watch?v=bNyUyrR0PHo","cat":"News","lang":"EN","desc":"International news 24/7"},
    {"name":"Euronews English","url":"https://www.youtube.com/watch?v=sPgqEHsONK8","cat":"News","lang":"EN","desc":"European news live"},
    {"name":"ABC News Live","url":"https://www.youtube.com/watch?v=w_Ma8oQLmSM","cat":"News","lang":"EN","desc":"ABC News 24/7"},
    {"name":"NBC News NOW","url":"https://www.youtube.com/watch?v=XOacA3R3wQ4","cat":"News","lang":"EN","desc":"NBC News live stream"},
    {"name":"CBS News 24/7","url":"https://www.youtube.com/watch?v=HsfQy6aiRkE","cat":"News","lang":"EN","desc":"CBS News live"},
    {"name":"Sky News","url":"https://www.youtube.com/watch?v=9Auq9mYxFEE","cat":"News","lang":"EN","desc":"Sky News live"},
    {"name":"WION Live","url":"https://www.youtube.com/watch?v=3tMDHSAs5Q0","cat":"News","lang":"EN","desc":"World is One News"},
    {"name":"Bloomberg TV","url":"https://www.youtube.com/watch?v=dp8PhLsUcFE","cat":"News","lang":"EN","desc":"Business & markets live"},
    # MUSIC
    {"name":"Lofi Girl Radio","url":"https://www.youtube.com/watch?v=jfKfPfyJRdk","cat":"Music","lang":"EN","desc":"24/7 lofi hip hop - study/relax"},
    {"name":"Synthwave Radio","url":"https://www.youtube.com/watch?v=MVPTGgRZq7E","cat":"Music","lang":"EN","desc":"Retro synthwave 24/7"},
    {"name":"Jazz Relax","url":"https://www.youtube.com/watch?v=Dx5qFachd3A","cat":"Music","lang":"EN","desc":"Smooth jazz music"},
    {"name":"Classical Music","url":"https://www.youtube.com/watch?v=MqynUQrQrRk","cat":"Music","lang":"EN","desc":"Classical music 24/7"},
    {"name":"Chillhop Radio","url":"https://www.youtube.com/watch?v=5yx6BWlEVcY","cat":"Music","lang":"EN","desc":"Chill beats to relax"},
    # NATURE & RELAXATION
    {"name":"NASA TV Live","url":"https://www.youtube.com/watch?v=21X5lGlDOfg","cat":"Science","lang":"EN","desc":"NASA live stream 24/7"},
    {"name":"ISS Live Earth","url":"https://www.youtube.com/watch?v=86YLFOog4GM","cat":"Science","lang":"EN","desc":"Earth from Space - ISS live"},
    {"name":"Nature 4K Scenes","url":"https://www.youtube.com/watch?v=niKbT1hQmkA","cat":"Nature","lang":"EN","desc":"Beautiful nature relaxation"},
    {"name":"Aquarium 4K","url":"https://www.youtube.com/watch?v=xTgUAtwqRbg","cat":"Nature","lang":"EN","desc":"Underwater aquarium 4K"},
    {"name":"Fireplace 4K","url":"https://www.youtube.com/watch?v=L_LUpnjgPso","cat":"Nature","lang":"EN","desc":"Cozy fireplace 4K"},
    {"name":"Ocean Waves","url":"https://www.youtube.com/watch?v=WHPEKLQJ1xw","cat":"Nature","lang":"EN","desc":"Ocean waves relaxing sounds"},
    {"name":"Rain Sounds","url":"https://www.youtube.com/watch?v=yIQdQ5UYtZU","cat":"Nature","lang":"EN","desc":"Rain sounds for sleep"},
    # ESPANOL
    {"name":"FRANCE 24 Espanol","url":"https://www.youtube.com/watch?v=9IBTZd9tAmA","cat":"News","lang":"ES","desc":"Noticias 24/7 en espanol"},
    {"name":"DW Espanol","url":"https://www.youtube.com/watch?v=58AIIjR2bL0","cat":"News","lang":"ES","desc":"Deutsche Welle en espanol"},
    {"name":"Euronews Espanol","url":"https://www.youtube.com/watch?v=UwcDqFwH0wo","cat":"News","lang":"ES","desc":"Euronews en espanol"},
    {"name":"RT en Espanol","url":"https://www.youtube.com/watch?v=6VXpOYj0vF4","cat":"News","lang":"ES","desc":"RT Noticias en espanol"},
    # ENTERTAINMENT
    {"name":"Funny Fails 24/7","url":"https://www.youtube.com/watch?v=VIDEO_ID","cat":"Entertainment","lang":"EN","desc":"Funny videos compilation"},
]

def load_favs():
    try:
        with open(FAVS_FILE,"r")as f:return json.load(f)
    except:return[]

def save_favs(favs):
    with open(FAVS_FILE,"w")as f:json.dump(favs,f)

class NexusTV:
    def __init__(self,root):
        self.root=root;root.title("NEXUS TV — Free Live Television");root.geometry("960x640");root.minsize(700,450);root.configure(bg=C["bg"])
        root.update_idletasks();x=(root.winfo_screenwidth()-960)//2;y=(root.winfo_screenheight()-640)//2;root.geometry(f"+{x}+{y}")
        self.favorites=load_favs()
        self.channels=CHANNELS
        self.current_cat="All"
        self._build()

    def _build(self):
        tk.Label(self.root,text="📺 NEXUS TV",font=("Segoe UI",20,"bold"),fg=C["accent"],bg=C["bg"]).pack(pady=(16,2))
        tk.Label(self.root,text="Free Live TV Channels • No Ads • No Signup",font=("Segoe UI",9),fg=C["dim"],bg=C["bg"]).pack()

        # Category tabs
        cat_f=tk.Frame(self.root,bg=C["bg"]);cat_f.pack(fill=tk.X,padx=16,pady=(8,0))
        cats=["All","News","Music","Nature","Science","Entertainment","Favorites"]
        self.cat_btns={}
        for cat in cats:
            btn=tk.Button(cat_f,text=cat,command=lambda c=cat:self._filter(c),font=("Segoe UI",9),bg=C["bg2"],fg=C["dim"],relief=tk.FLAT,padx=12,pady=4,cursor="hand2",activebackground=C["card"],activeforeground=C["text"])
            btn.pack(side=tk.LEFT,padx=1);self.cat_btns[cat]=btn
        self.cat_btns["All"].config(bg=C["accent"],fg="#fff")

        # Channel grid
        self.canvas=tk.Canvas(self.root,bg=C["bg"],highlightthickness=0)
        self.sbar=ttk.Scrollbar(self.root,orient="vertical",command=self.canvas.yview)
        self.grid_f=tk.Frame(self.canvas,bg=C["bg"])
        self.grid_f.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0),window=self.grid_f,anchor="nw");self.canvas.configure(yscrollcommand=self.sbar.set)
        self.canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=True);self.sbar.pack(side=tk.RIGHT,fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>",lambda e:self.canvas.yview_scroll(int(-e.delta/40),"units"))

        self._render()
        tk.Label(self.root,text=f"📺 {len(CHANNELS)} channels • Click any channel to watch • Free & Legal",
                font=("Segoe UI",8),fg=C["dim"],bg=C["bg"]).pack(side=tk.BOTTOM,fill=tk.X,padx=16,pady=6)

    def _filter(self,cat):
        self.current_cat=cat
        for c,btn in self.cat_btns.items():btn.config(bg=C["bg2"],fg=C["dim"])
        if cat in self.cat_btns:self.cat_btns[cat].config(bg=C["accent"],fg="#fff")
        self._render()

    def _render(self):
        for w in self.grid_f.winfo_children():w.destroy()
        favs=load_favs()

        if self.current_cat=="Favorites":
            channels=[c for c in self.channels if c["name"]in favs]
        else:
            channels=self.channels if self.current_cat=="All" else[c for c in self.channels if c["cat"]==self.current_cat]

        if not channels:
            tk.Label(self.grid_f,text="No channels found",font=("Segoe UI",12),fg=C["dim"],bg=C["bg"]).pack(expand=True,pady=60);return

        w=max(700,self.canvas.winfo_width()-20);cols=max(2,w//290)
        for i,ch in enumerate(channels):
            row,col=i//cols,i%cols;pad=8;x=col*(270+pad)+pad;y=row*(140+pad)+pad

            card=tk.Frame(self.grid_f,bg=C["card"],highlightbackground=C["border"],highlightthickness=1,cursor="hand2")
            card.place(x=x,y=y,width=270,height=140)

            # Live badge
            live_color=C["live"]if ch["cat"]=="News"else C["green"]
            tk.Label(card,text=" ● LIVE ",font=("Segoe UI",7,"bold"),fg=live_color,bg=C["card"]).place(x=6,y=4)

            # Category badge
            cat_colors={"News":C["accent"],"Music":C["blue"],"Nature":C["green"],"Science":C["gold"],"Entertainment":C["accent2"]}
            tk.Label(card,text=f" {ch['cat']} ",font=("Segoe UI",7),fg="#fff",bg=cat_colors.get(ch["cat"],C["dim"])).place(relx=1,x=-6,y=4,anchor="ne")

            # Channel name
            tk.Label(card,text=ch["name"],font=("Segoe UI",11,"bold"),fg=C["text"],bg=C["card"],anchor="w").place(x=10,y=30)
            tk.Label(card,text=ch.get("desc",""),font=("Segoe UI",8),fg=C["dim"],bg=C["card"],wraplength=240,anchor="w",justify="left").place(x=10,y=55)

            # Language
            if ch.get("lang"):tk.Label(card,text=ch["lang"],font=("Segoe UI",7),fg=C["dim"],bg=C["card"]).place(x=10,y=110)

            # Watch button
            watch=tk.Label(card,text="▶ WATCH",font=("Segoe UI",9,"bold"),fg=C["accent"],bg=C["card"],cursor="hand2")
            watch.place(x=10,y=112)if not ch.get("lang")else watch.place(x=35,y=110)
            watch.bind("<Button-1>",lambda e,u=ch["url"]:self._play(u))
            card.bind("<Button-1>",lambda e,u=ch["url"]:self._play(u))

            # Favorite
            is_fav=ch["name"]in favs
            heart=tk.Label(card,text="❤️"if is_fav else"🤍",font=("Segoe UI",11),bg=C["card"],fg=C["accent"]if is_fav else C["dim"],cursor="hand2")
            heart.place(relx=1,x=-10,y=112)
            heart.bind("<Button-1>",lambda e,n=ch["name"]:self._toggle_fav(n))

    def _play(self,url):
        try:
            subprocess.Popen(["cmd","/c","start","msedge",f"--app={url}","--window-size=960,600","--new-window"],shell=True,creationflags=subprocess.CREATE_NO_WINDOW)
        except:webbrowser.open(url)

    def _toggle_fav(self,name):
        favs=load_favs()
        if name in favs:favs.remove(name)
        else:favs.append(name)
        save_favs(favs)
        self.favorites=favs
        self._render()

def main():
    root=tk.Tk();NexusTV(root);root.mainloop()

if __name__=="__main__":main()
