"""
NEXUS EXTRACTOR PRO v1.0 — Web Intelligence & Data Extraction
Emails, links, images, documents, metadata, source, APIs, security. 100% legal.
"""
import os, sys, json, re, threading, time, urllib.request, urllib.parse, ssl, csv, shutil
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try: from bs4 import BeautifulSoup; HAS_BS4=True
except: HAS_BS4=False
try: import requests; HAS_REQ=True
except: HAS_REQ=False

C={"bg":"#0a0a12","bg2":"#121225","card":"#1a1a35","border":"#1e1e42","text":"#d0d0e4","dim":"#484870","accent":"#f59e0b","accent2":"#fbbf24","green":"#34d399","red":"#f87171","blue":"#60a5fa"}
DATA_DIR=Path.home()/"Documents"/"NexusExtractor";DATA_DIR.mkdir(parents=True,exist_ok=True)
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"

def http_get(url,timeout=12):
    if HAS_REQ:
        try: r=requests.get(url,headers={"User-Agent":UA},timeout=timeout);return r.text,r.status_code,dict(r.headers),None
        except Exception as e:return"",0,{},str(e)
    try:
        ctx=ssl.create_default_context();req=urllib.request.Request(url,headers={"User-Agent":UA})
        with urllib.request.urlopen(req,timeout=timeout,context=ctx)as resp:return resp.read().decode(errors="ignore"),resp.status,dict(resp.info()),None
    except Exception as e:return"",0,{},str(e)

class NexusExtractor:
    def __init__(self,root):
        self.root=root;root.title("NEXUS EXTRACTOR PRO");root.geometry("900x620");root.minsize(680,450);root.configure(bg=C["bg"])
        root.update_idletasks();x=(root.winfo_screenwidth()-900)//2;y=(root.winfo_screenheight()-620)//2;root.geometry(f"+{x}+{y}")
        self.results={};self.current_url="";self._build()

    def _build(self):
        tk.Label(self.root,text="🕸️ NEXUS EXTRACTOR PRO — Web Intelligence",font=("Segoe UI",16,"bold"),fg=C["accent2"],bg=C["bg"]).pack(pady=(12,4))

        inp_f=tk.Frame(self.root,bg=C["bg2"],highlightbackground=C["border"],highlightthickness=1);inp_f.pack(fill=tk.X,padx=16,pady=(4,0))
        inner=tk.Frame(inp_f,bg=C["bg2"]);inner.pack(fill=tk.X,padx=10,pady=8)
        tk.Label(inner,text="URL:",font=("Segoe UI",9,"bold"),fg=C["dim"],bg=C["bg2"]).pack(side=tk.LEFT)
        self.url_e=tk.Entry(inner,font=("Consolas",11),bg=C["bg"],fg=C["text"],insertbackground=C["accent"],relief=tk.FLAT,width=40,borderwidth=0)
        self.url_e.pack(side=tk.LEFT,padx=8,fill=tk.X,expand=True,ipady=5);self.url_e.insert(0,"https://");self.url_e.bind("<Return>",lambda e:self._extract())
        self.extract_btn=tk.Button(inner,text="🕸️ EXTRACT",command=self._extract,font=("Segoe UI",10,"bold"),bg=C["accent"],fg="#000",relief=tk.FLAT,padx=16,pady=5,cursor="hand2");self.extract_btn.pack(side=tk.LEFT,padx=4)

        nb=ttk.Notebook(self.root);nb.pack(fill=tk.BOTH,expand=True,padx=16,pady=(6,8))
        st=ttk.Style();st.theme_use("clam");st.configure("TNotebook",background=C["bg"],borderwidth=0);st.configure("TNotebook.Tab",background=C["bg2"],foreground=C["dim"],padding=[10,5],font=("Segoe UI",9));st.map("TNotebook.Tab",background=[("selected",C["bg"])],foreground=[("selected",C["accent"])])
        self.tabs={}
        for label in["Overview","Emails","Links","Images","Documents","Metadata","Source","APIs","Security"]:
            tab=tk.Frame(nb,bg=C["bg"]);nb.add(tab,text=f"  {label}  ")
            tree=ttk.Treeview(tab,show="headings",selectmode="extended",height=10);tree.pack(fill=tk.BOTH,expand=True,padx=4,pady=4)
            st2=ttk.Style();st2.configure("Treeview",background=C["bg2"],foreground=C["text"],fieldbackground=C["bg2"],rowheight=24,font=("Segoe UI",8))
            sb=ttk.Scrollbar(tab,command=tree.yview);tree.configure(yscrollcommand=sb.set);tree.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
            self.tabs[label.lower()]=tree

        bot=tk.Frame(self.root,bg=C["bg2"],height=30);bot.pack(fill=tk.X,side=tk.BOTTOM);bot.pack_propagate(False)
        self.status_lbl=tk.Label(bot,text="Enter URL and click EXTRACT",font=("Segoe UI",8),fg=C["dim"],bg=C["bg2"]);self.status_lbl.pack(side=tk.LEFT,padx=14,pady=4)
        for text,cmd in[("💾 Save Page",self._save_page),("📄 Export CSV",self._export_csv),("📋 Export JSON",self._export_json)]:
            tk.Button(bot,text=text,command=cmd,font=("Segoe UI",8),bg=C["bg2"],fg=C["text"],relief=tk.FLAT,padx=10,cursor="hand2").pack(side=tk.RIGHT,pady=2)

    def _extract(self):
        url=self.url_e.get().strip()
        if not url.startswith("http"):url="https://"+url
        self.current_url=url;self.extract_btn.config(text="⏳ EXTRACTING...",state=tk.DISABLED,bg=C["bg2"],fg=C["dim"])
        self.status_lbl.config(text=f"Extracting {url}...",fg=C["accent"])
        for tree in self.tabs.values():tree.delete(*tree.get_children())
        self.results={}

        def _run():
            html,status,headers,err=http_get(url)
            if err:self.root.after(0,lambda:self._error(f"HTTP Error: {err}"));return
            soup=BeautifulSoup(html,"html.parser")if HAS_BS4 and html else None
            self._extract_all(html,soup,url,headers,status)
            self.root.after(0,self._show_all)
        threading.Thread(target=_run,daemon=True).start()

    def _extract_all(self,html,soup,url,headers,status):
        r=self.results;domain=urllib.parse.urlparse(url).netloc
        title=soup.title.get_text(strip=True)if soup and soup.title else"No title"
        r["overview"]=[("URL",url),("Title",title),("Status",str(status)),("Server",headers.get("Server","N/A")),("Content-Type",headers.get("Content-Type","N/A")),("Page Size",f"{len(html)/1024:.1f} KB")]
        if soup:r["overview"]+=[("Links",str(len(soup.find_all("a",href=True)))),("Images",str(len(soup.find_all("img",src=True)))),("Scripts",str(len(soup.find_all("script",src=True)))),("Forms",str(len(soup.find_all("form"))))]
        r["emails"]=[(e,)for e in list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',html)))[:50]]
        links_data=[];images_data=[];docs=[]
        if soup:
            for a in soup.find_all("a",href=True):
                href=a["href"]
                if href.startswith("/"):href=urllib.parse.urljoin(url,href)
                links_data.append((href[:150],a.get_text(strip=True)[:80]))
                hlow=href.lower()
                for ext in[".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".csv",".zip",".sql",".bak",".json"]:
                    if hlow.endswith(ext):docs.append((os.path.basename(href),href[:150],ext));break
            for img in soup.find_all("img",src=True):
                src=img["src"]
                if src.startswith("/"):src=urllib.parse.urljoin(url,src)
                images_data.append((src[:150],img.get("alt","")[:60]))
        r["links"]=links_data[:100];r["images"]=images_data[:50];r["documents"]=docs[:50]
        meta=[]
        if soup:
            for tag in soup.find_all("meta"):
                name=tag.get("name")or tag.get("property")or tag.get("http-equiv")or""
                content=tag.get("content","")
                if name and content:meta.append((name,content[:200]))
        r["metadata"]=meta[:30]
        r["source"]=[(f"Line {i+1}",l[:200])for i,l in enumerate(html.split("\n")[:50])]
        apis=[]
        for p in[r'/api/v\d+/[\w/]+',r'/graphql',r'/rest/[\w/]+',r'/wp-json/[\w/]+',r'\.json\b']:
            for m in re.finditer(p,html):
                g=m.group(0)
                if not g.startswith("http"):g=urllib.parse.urljoin(url,g)
                apis.append((g[:150],"API Pattern"))
        r["apis"]=list({a[0]:a for a in apis}.values())[:30]
        sec=[]
        sec.append(("HTTPS","Enabled"if url.startswith("https")else"NOT HTTPS"))
        sec.append(("HSTS",headers.get("Strict-Transport-Security","Missing")[:80]))
        sec.append(("CSP",headers.get("Content-Security-Policy","Missing")[:100]))
        sec.append(("X-Frame-Options",headers.get("X-Frame-Options","Missing")))
        sec.append(("Server",headers.get("Server","Not exposed")))
        r["security"]=sec

    def _show_all(self):
        self.extract_btn.config(text="🕸️ EXTRACT",state=tk.NORMAL,bg=C["accent"],fg="#000")
        total=sum(len(v)for v in self.results.values());self.status_lbl.config(text=f"Extracted {total} items",fg=C["green"])
        for label,cols,widths,data in[
            ("overview",("k","v"),(150,500),self.results.get("overview",[])),
            ("emails",("email",),(600,),self.results.get("emails",[])),
            ("links",("url","text"),(400,250),self.results.get("links",[])),
            ("images",("url","alt"),(400,250),self.results.get("images",[])),
            ("documents",("name","url","ext"),(150,400,60),self.results.get("documents",[])),
            ("metadata",("name","content"),(150,500),self.results.get("metadata",[])),
            ("source",("line","code"),(60,600),self.results.get("source",[])),
            ("apis",("url","type"),(400,200),self.results.get("apis",[])),
            ("security",("check","status"),(200,400),self.results.get("security",[])),
        ]:
            t=self.tabs[label];t["columns"]=cols
            for i,c in enumerate(cols):t.heading(c,text=c.title());t.column(c,width=widths[i]if i<len(widths)else 200)
            for row in data:
                if isinstance(row,tuple):t.insert("",tk.END,values=row)

    def _error(self,msg):self.extract_btn.config(text="🕸️ EXTRACT",state=tk.NORMAL,bg=C["accent"],fg="#000");self.status_lbl.config(text=msg[:80],fg=C["red"])

    def _save_page(self):
        if not self.current_url:return
        html,_,_,_=http_get(self.current_url)
        fp=filedialog.asksaveasfilename(defaultextension=".html",filetypes=[("HTML","*.html")],initialfile="page.html")
        if fp:
            with open(fp,"w",encoding="utf-8")as f:f.write(html)
            messagebox.showinfo("Saved",f"Page saved to:\n{fp}")

    def _export_csv(self):
        if not self.results:return
        fp=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile="extract.csv")
        if not fp:return
        with open(fp,"w",newline="",encoding="utf-8")as f:
            w=csv.writer(f)
            for cat,data in self.results.items():
                w.writerow([f"=== {cat.upper()} ==="])
                for row in data:w.writerow(row)
        messagebox.showinfo("Exported",f"CSV saved to:\n{fp}")

    def _export_json(self):
        if not self.results:return
        fp=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],initialfile="extract.json")
        if not fp:return
        export={"url":self.current_url,"date":datetime.now().isoformat(),"results":{k:list(v)for k,v in self.results.items()}}
        with open(fp,"w",encoding="utf-8")as f:json.dump(export,f,indent=2,ensure_ascii=False)
        messagebox.showinfo("Exported",f"JSON saved to:\n{fp}")

def main():
    root=tk.Tk();NexusExtractor(root);root.mainloop()

if __name__=="__main__":main()
