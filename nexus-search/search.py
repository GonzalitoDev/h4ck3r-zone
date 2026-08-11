"""
NEXUS SEARCH PRO v1.0 — Multi-Engine Legal Search
Searches Google, Reddit, StackOverflow, GitHub, Wikipedia, DuckDuckGo simultaneously.
100% legal. Open source and forum search aggregator.
"""
import os, sys, json, threading, urllib.request, urllib.parse, re, ssl, webbrowser
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

try: from bs4 import BeautifulSoup; HAS_BS4=True
except: HAS_BS4=False
try: import requests; HAS_REQ=True
except: HAS_REQ=False

C={"bg":"#080810","bg2":"#101022","card":"#181830","border":"#1e1e42","text":"#d0d0e4","dim":"#484870","accent":"#f59e0b","accent2":"#fbbf24","green":"#34d399","red":"#f87171","orange":"#fb923c","blue":"#60a5fa","purple":"#a855f7","pink":"#ec4899"}

DATA_DIR=Path.home()/"Documents"/"NexusSearch"
DATA_DIR.mkdir(parents=True,exist_ok=True)
HISTORY_FILE=DATA_DIR/"history.json"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"

SEARCH_ENGINES={
    # Surface Web
    "Google":"https://www.google.com/search?q=",
    "DuckDuckGo":"https://duckduckgo.com/html/?q=",
    "Reddit":"https://www.reddit.com/search/?q=",
    "StackOverflow":"https://stackoverflow.com/search?q=",
    "GitHub":"https://github.com/search?q=",
    "Wikipedia":"https://en.wikipedia.org/w/index.php?search=",
    # Safe Deep Web — Academic, Government, Legal
    "Google Scholar":"https://scholar.google.com/scholar?q=",
    "arXiv":"https://arxiv.org/search/?query=",
    "PubMed":"https://pubmed.ncbi.nlm.nih.gov/?term=",
    "Internet Archive":"https://archive.org/search.php?query=",
    "Project Gutenberg":"https://www.gutenberg.org/ebooks/search/?query=",
    "PublicWWW":"https://publicwww.com/websites/",
    "CORE.ac.uk":"https://core.ac.uk/search?q=",
    "Data.gov":"https://catalog.data.gov/dataset?q=",
    "WHOIS":"https://www.whois.com/whois/",
    "Exploit-DB":"https://www.exploit-db.com/search?q=",
    "OpenAlex":"https://openalex.org/works?search=",
}

def load_history():
    try:
        with open(HISTORY_FILE,"r")as f:return json.load(f)
    except:return[]

def save_history(data):
    with open(HISTORY_FILE,"w")as f:json.dump(data[-50:],f)

def http_get(url,timeout=8):
    if HAS_REQ:
        try:r=requests.get(url,headers={"User-Agent":UA},timeout=timeout);return r.text,r.status_code,None
        except Exception as e:return"",0,str(e)
    try:
        ctx=ssl.create_default_context();req=urllib.request.Request(url,headers={"User-Agent":UA})
        with urllib.request.urlopen(req,timeout=timeout,context=ctx)as resp:return resp.read().decode(errors="ignore"),resp.status,None
    except Exception as e:return"",0,str(e)

def search_google(query):
    results=[]
    html,status,err=http_get(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    if status==200 and HAS_BS4:
        soup=BeautifulSoup(html,"html.parser")
        for g in soup.find_all("div",class_="g")[:8]:
            try:
                a=g.find("a");h3=g.find("h3")
                if a and h3:
                    url=a.get("href","")
                    if url.startswith("/url?"):
                        m=re.search(r'url\?q=([^&]+)',url)
                        if m:url=urllib.parse.unquote(m.group(1))
                    results.append({"title":h3.get_text(strip=True),"url":url[:200],"source":"Google","snippet":""})
            except:pass
    return results

def search_stack(query):
    results=[]
    html,status,err=http_get(f"https://stackoverflow.com/search?q={urllib.parse.quote(query)}")
    if status==200 and HAS_BS4:
        soup=BeautifulSoup(html,"html.parser")
        for r in soup.find_all("div",class_="s-result")[:8]:
            try:
                a=r.find("a",class_="s-link")
                if a:
                    title=a.get_text(strip=True)
                    url="https://stackoverflow.com"+a.get("href","")
                    exc=r.find("span",class_="excerpt")
                    snippet=exc.get_text(strip=True)[:150]if exc else""
                    results.append({"title":title,"url":url,"source":"StackOverflow","snippet":snippet})
            except:pass
    return results

def search_reddit(query):
    results=[]
    html,status,err=http_get(f"https://www.reddit.com/search/?q={urllib.parse.quote(query)}")
    if status==200 and HAS_BS4:
        soup=BeautifulSoup(html,"html.parser")
        for post in soup.find_all("shreddit-post")[:8]:
            try:
                title=post.get("post-title","")
                url="https://reddit.com"+post.get("permalink","")
                results.append({"title":title[:120],"url":url,"source":"Reddit","snippet":""})
            except:pass
    return results

def search_github(query):
    results=[]
    html,status,err=http_get(f"https://github.com/search?q={urllib.parse.quote(query)}&type=repositories")
    if status==200 and HAS_BS4:
        soup=BeautifulSoup(html,"html.parser")
        for r in soup.find_all("div",{"data-testid":"results-list"})[:1]:
            for item in r.find_all("div",class_=re.compile("search-title"))[:8]:
                try:
                    a=item.find("a")
                    if a:
                        title=" ".join(a.get_text(strip=True).split())
                        url="https://github.com"+a.get("href","")
                        results.append({"title":title[:120],"url":url,"source":"GitHub","snippet":""})
                except:pass
    return results


def search_archive(query):
    results=[]
    try:
        data=json.loads(http_get(f"https://archive.org/advancedsearch.php?q={urllib.parse.quote(query)}&fl[]=identifier,title,description&rows=8&output=json")[0])
        for doc in data.get("response",{}).get("docs",[]):
            identifier=doc.get("identifier","");title=doc.get("title","Unknown");desc=(doc.get("description","")or"")[:150]
            if identifier:results.append({"title":title[:120],"url":f"https://archive.org/details/{identifier}","source":"Internet Archive","snippet":desc})
    except:pass
    return results

def search_arxiv(query):
    results=[]
    try:
        data=http_get(f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results=8")[0]
        if data:
            for entry in data.split("<entry>")[1:]:
                tm=re.search(r'<title>(.*?)</title>',entry,re.DOTALL);um=re.search(r'<id>(.*?)</id>',entry);sm=re.search(r'<summary>(.*?)</summary>',entry,re.DOTALL)
                if tm and um:results.append({"title":tm.group(1).strip().replace("\n"," ")[:120],"url":um.group(1).strip(),"source":"arXiv","snippet":(sm.group(1).strip()[:150]if sm else"")})
    except:pass
    return results

class NexusSearch:
    def __init__(self,root):
        self.root=root;root.title("NEXUS SEARCH PRO — Multi-Engine Search");root.geometry("900x620");root.minsize(650,450);root.configure(bg=C["bg"])
        root.update_idletasks();x=(root.winfo_screenwidth()-900)//2;y=(root.winfo_screenheight()-620)//2;root.geometry(f"+{x}+{y}")
        self.history=load_history();self.results=[];self._build()

    def _build(self):
        hdr=tk.Frame(self.root,bg=C["bg"]);hdr.pack(fill=tk.X,padx=16,pady=(12,0))
        tk.Label(hdr,text="🔍 NEXUS SEARCH PRO",font=("Segoe UI",18,"bold"),fg=C["accent2"],bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr,text="Multi-Engine Legal Search",font=("Segoe UI",9),fg=C["dim"],bg=C["bg"]).pack(side=tk.LEFT,padx=10,pady=(5,0))

        # Search bar
        sf=tk.Frame(self.root,bg=C["bg2"],highlightbackground=C["border"],highlightthickness=1);sf.pack(fill=tk.X,padx=16,pady=(8,0))
        inner=tk.Frame(sf,bg=C["bg2"]);inner.pack(fill=tk.X,padx=10,pady=8)
        tk.Label(inner,text="🔍",font=("Segoe UI",14),fg=C["accent"],bg=C["bg2"]).pack(side=tk.LEFT)
        self.query_e=tk.Entry(inner,font=("Segoe UI",13),bg=C["bg"],fg=C["text"],insertbackground=C["accent"],relief=tk.FLAT,width=40,borderwidth=0)
        self.query_e.pack(side=tk.LEFT,padx=8,fill=tk.X,expand=True,ipady=6)
        self.query_e.bind("<Return>",lambda e:self._search())
        self.search_btn=tk.Button(inner,text="SEARCH",command=self._search,font=("Segoe UI",11,"bold"),bg=C["accent"],fg="#000",relief=tk.FLAT,padx=18,pady=6,cursor="hand2");self.search_btn.pack(side=tk.LEFT,padx=4)

        # Engine toggles
        tf=tk.Frame(self.root,bg=C["bg"]);tf.pack(fill=tk.X,padx=16,pady=(4,0))
        self.engine_vars={}
        engines_ui=[
            ("🌐 Google",C["blue"]),("🦆 DuckDuckGo",C["orange"]),("💬 Reddit",C["red"]),
            ("📚 StackOverflow",C["orange"]),("🐙 GitHub",C["purple"]),("📖 Wikipedia",C["dim"]),
            # Deep Web — Safe & Legal
            ("🎓 Scholar",C["green"]),("📄 arXiv",C["green"]),("🏥 PubMed",C["green"]),
            ("📦 Archive.org",C["gold"]),("📕 Gutenberg",C["gold"]),("💻 PublicWWW",C["blue"]),
            ("🔬 CORE",C["green"]),("🏛️ Data.gov",C["blue"]),("🔍 WHOIS",C["accent"]),
            ("🛡️ Exploit-DB",C["red"]),("📊 OpenAlex",C["green"]),
        ]
        row_frame=None
        for i,(name,color)in enumerate(engines_ui):
            if i%6==0:row_frame=tk.Frame(tf,bg=C["bg"]);row_frame.pack(fill=tk.X)
            engine_key=name.split(" ",1)[1]if" "in name else name
            var=tk.BooleanVar(value=engine_key in["Google","Reddit","StackOverflow","GitHub","Scholar","Archive.org"])
            self.engine_vars[engine_key]=var
            tk.Checkbutton(row_frame,text=name,variable=var,bg=C["bg"],fg=color,selectcolor=C["bg2"],activebackground=C["bg"],font=("Segoe UI",7)).pack(side=tk.LEFT,padx=1)

        # Results
        self.result_frame=tk.Frame(self.root,bg=C["bg"]);self.result_frame.pack(fill=tk.BOTH,expand=True,padx=16,pady=(6,8))
        canvas=tk.Canvas(self.result_frame,bg=C["bg"],highlightthickness=0)
        sbar=ttk.Scrollbar(self.result_frame,command=canvas.yview)
        self.results_f=tk.Frame(canvas,bg=C["bg"])
        self.results_f.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=self.results_f,anchor="nw",width=850)
        canvas.configure(yscrollcommand=sbar.set);canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=True);sbar.pack(side=tk.RIGHT,fill=tk.Y)
        canvas.bind_all("<MouseWheel>",lambda e:canvas.yview_scroll(int(-e.delta/30),"units"))

        tk.Label(self.results_f,text="Enter a search query above and press SEARCH\n\nGoogle + Reddit + StackOverflow + GitHub + Wikipedia...",font=("Segoe UI",12),fg=C["dim"],bg=C["bg"]).pack(expand=True,pady=80)

        self.status_lbl=tk.Label(self.root,text=f"Ready • {len(SEARCH_ENGINES)} engines available",font=("Segoe UI",8),fg=C["dim"],bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM,fill=tk.X,padx=16,pady=6)

    def _search(self):
        query=self.query_e.get().strip()
        if not query:return
        self.search_btn.config(text="⏳ SEARCHING...",state=tk.DISABLED,bg=C["bg2"],fg=C["dim"])
        self.status_lbl.config(text=f"Searching: {query}...",fg=C["accent"])

        # Save to history
        self.history.insert(0,{"query":query,"date":datetime.now().isoformat()});save_history(self.history)

        # Clear results (keep placeholder)
        for w in self.results_f.winfo_children():w.destroy()
        tk.Label(self.results_f,text=f"🔍 Searching '{query}' across multiple engines...",font=("Segoe UI",11),fg=C["accent"],bg=C["bg"]).pack(pady=14)
        progress=ttk.Progressbar(self.results_f,mode="indeterminate",length=200);progress.pack(pady=4);progress.start(8)

        self.results=[]
        engines_to_search=[e for e,v in self.engine_vars.items()if v.get()]
        if not engines_to_search:engines_to_search=["Google"]

        def _run():
            all_results=[]
            def _add(source,results):
                all_results.extend(results)
                self.root.after(0,lambda:progress.configure(value=len(all_results)*5))
            threads=[]
            for engine in engines_to_search:
                if engine=="Google":
                    t=threading.Thread(target=lambda:_add("Google",search_google(query)),daemon=True);t.start();threads.append(t)
                elif engine=="StackOverflow":
                    t=threading.Thread(target=lambda:_add("StackOverflow",search_stack(query)),daemon=True);t.start();threads.append(t)
                elif engine=="Reddit":
                    t=threading.Thread(target=lambda:_add("Reddit",search_reddit(query)),daemon=True);t.start();threads.append(t)
                elif engine=="GitHub":
                    t=threading.Thread(target=lambda:_add("GitHub",search_github(query)),daemon=True);t.start();threads.append(t)
                elif engine=="Scholar":
                    all_results.append({"title":f"Search on Google Scholar: {query}","url":f"https://scholar.google.com/scholar?q={urllib.parse.quote(query)}","source":"Google Scholar","snippet":"Academic papers, theses, books"})
                elif engine=="Archive.org":
                    t=threading.Thread(target=lambda:_add("Internet Archive",search_archive(query)),daemon=True);t.start();threads.append(t)
                elif engine=="arXiv":
                    t=threading.Thread(target=lambda:_add("arXiv",search_arxiv(query)),daemon=True);t.start();threads.append(t)
                else:
                    # Direct link for other engines
                    url=SEARCH_ENGINES.get(engine,"")+urllib.parse.quote(query)
                    all_results.append({"title":f"Search on {engine}","url":url,"source":engine,"snippet":f"Open {engine} search in browser"})
            for t in threads:t.join(timeout=8)
            self.results=all_results
            self.root.after(0,lambda:self._show_results(query,progress))

        threading.Thread(target=_run,daemon=True).start()

    def _show_results(self,query,progress):
        for w in self.results_f.winfo_children():w.destroy()
        self.search_btn.config(text="SEARCH",state=tk.NORMAL,bg=C["accent"],fg="#000")
        total=len(self.results)
        self.status_lbl.config(text=f"✅ {total} results for '{query}'",fg=C["green"])

        if not self.results:
            tk.Label(self.results_f,text="No results found.\nTry different keywords or check your internet connection.",font=("Segoe UI",12),fg=C["dim"],bg=C["bg"]).pack(expand=True,pady=60);return

        source_colors={"Google":C["blue"],"StackOverflow":C["orange"],"Reddit":C["red"],"GitHub":C["purple"],"Wikipedia":C["dim"],"DuckDuckGo":C["orange"],"Google Scholar":C["green"],"Internet Archive":C["gold"],"arXiv":C["green"],"Bing":C["blue"],"Medium":C["dim"],"Dev.to":C["dim"]}

        for i,r in enumerate(self.results):
            card=tk.Frame(self.results_f,bg=C["card"],highlightbackground=C["border"],highlightthickness=1,cursor="hand2")
            card.pack(fill=tk.X,padx=2,pady=2)
            card.bind("<Button-1>",lambda e,u=r["url"]:webbrowser.open(u))

            header=tk.Frame(card,bg=C["card"]);header.pack(fill=tk.X,padx=12,pady=(8,0))
            tk.Label(header,text=f"[{r['source']}]",font=("Segoe UI",8,"bold"),fg=source_colors.get(r["source"],C["dim"]),bg=C["card"]).pack(side=tk.LEFT)
            tk.Label(header,text=r["title"][:100],font=("Segoe UI",10,"bold"),fg=C["text"],bg=C["card"],anchor="w",wraplength=700,justify="left").pack(side=tk.LEFT,padx=6)

            if r.get("snippet"):
                tk.Label(card,text=r["snippet"][:200],font=("Segoe UI",8),fg=C["dim"],bg=C["card"],anchor="w",wraplength=750,justify="left").pack(fill=tk.X,padx=30,pady=(2,6))

            tk.Label(card,text=r["url"][:100],font=("Segoe UI",7),fg=C["dim"],bg=C["card"],anchor="w").pack(fill=tk.X,padx=30,pady=(0,8))


def main():
    root=tk.Tk();NexusSearch(root);root.mainloop()

if __name__=="__main__":main()
