"""
NEXUS PAGE MONITOR v1.0 — 24/7 Website Health Monitor
Monitors uptime, response time, SSL, content changes, alerts.
System tray mode. Auto-start. Beautiful dashboard.
"""
import os,sys,json,threading,time,ssl,socket,urllib.request,re,hashlib
from datetime import datetime,timedelta
from pathlib import Path
from collections import deque

import tkinter as tk
from tkinter import ttk,messagebox

try:import requests;HAS_REQ=True
except:HAS_REQ=False

C={"bg":"#080810","bg2":"#101022","card":"#181830","border":"#1e1e42","text":"#d0d0e4","dim":"#484870","accent":"#6366f1","accent2":"#818cf8","green":"#34d399","red":"#f87171","orange":"#fb923c","gold":"#fbbf24","blue":"#60a5fa"}

DATA_DIR=Path.home()/"Documents"/"NexusMonitor";DATA_DIR.mkdir(parents=True,exist_ok=True)
LOG_FILE=DATA_DIR/"monitor_log.json"

URL="https://gonzalitodev.github.io/h4ck3r-zone/websecurity-landing/"
CHECK_INTERVAL=5 # seconds

def load_log():
    try:
        with open(LOG_FILE)as f:return json.load(f)
    except:return{"checks":0,"uptime_pct":100,"downtimes":[],"history":[],"last_content":"","last_deploy":""}

def save_log(data):
    data["history"]=data["history"][-200:]
    with open(LOG_FILE,"w")as f:json.dump(data,f)

def check_page():
    start=time.time()
    result={"time":datetime.now().isoformat(),"online":False,"status":0,"response_ms":0,"size_kb":0,"error":"","content_changed":False,"ssl_ok":False,"ssl_days":0}

    try:
        ctx=ssl.create_default_context()
        ctx.check_hostname=True
        parsed=urllib.parse.urlparse(URL)
        host=parsed.netloc

        # SSL check
        sock=socket.socket();sock.settimeout(5)
        ssock=ctx.wrap_socket(sock,server_hostname=host)
        ssock.connect((host,443))
        cert=ssock.getpeercert();ssock.close()
        not_after=cert.get("notAfter","")
        try:
            exp=datetime.strptime(not_after,"%b %d %H:%M:%S %Y %Z")
            result["ssl_days"]=(exp-datetime.now()).days
            result["ssl_ok"]=result["ssl_days"]>0
        except:pass
    except:pass

    # HTTP check
    try:
        req=urllib.request.Request(URL,headers={"User-Agent":"NexusMonitor/1.0"})
        resp=urllib.request.urlopen(req,timeout=10)
        content=resp.read().decode(errors="ignore")
        result["online"]=True
        result["status"]=resp.status
        result["size_kb"]=round(len(content)/1024,1)
        result["response_ms"]=round((time.time()-start)*1000)

        # Version check
        m=re.search(r'<meta name="nexus-version" content="([^"]+)"',content)
        if m:result["version"]=m.group(1)

        # Content change
        log=load_log()
        if log.get("last_content"):
            old_hash=log["last_content"]
            new_hash=hashlib.md5(content.encode()).hexdigest()
            result["content_changed"]=old_hash!=new_hash
            if result["content_changed"]:
                log["last_deploy"]=datetime.now().isoformat()
        log["last_content"]=hashlib.md5(content.encode()).hexdigest()
        save_log(log)
    except Exception as e:
        result["error"]=str(e)[:100]

    # Save to log
    log=load_log()
    log["checks"]+=1
    log["history"].append(result)
    if result["online"]:log["uptime_pct"]=round(sum(1 for h in log["history"]if h["online"])/max(len(log["history"]),1)*100,1)
    else:
        if not log["downtimes"]or(log["downtimes"][-1].get("end")):
            log["downtimes"].append({"start":datetime.now().isoformat(),"end":"","duration":"","reason":result["error"]})
    save_log(log)
    return result


class NexusMonitor:
    def __init__(self,root):
        self.root=root;root.title("NEXUS PAGE MONITOR");root.geometry("700x520");root.minsize(500,380);root.configure(bg=C["bg"])
        root.update_idletasks();x=(root.winfo_screenwidth()-700)//2;y=(root.winfo_screenheight()-520)//2;root.geometry(f"+{x}+{y}")
        self.log=load_log();self.running=False;self._build();self._start()

    def _build(self):
        tk.Label(self.root,text="📊 NEXUS PAGE MONITOR",font=("Segoe UI",17,"bold"),fg=C["accent2"],bg=C["bg"]).pack(pady=(12,2))
        tk.Label(self.root,text=f"Monitoring: {URL}",font=("Segoe UI",8),fg=C["dim"],bg=C["bg"])

        # Status card
        card=tk.Frame(self.root,bg=C["card"],highlightbackground=C["border"],highlightthickness=1);card.pack(fill=tk.X,padx=16,pady=(8,0))
        inner=tk.Frame(card,bg=C["card"]);inner.pack(padx=12,pady=10)
        self.status_dot=tk.Canvas(inner,width=16,height=16,bg=C["card"],highlightthickness=0);self.status_dot.pack(side=tk.LEFT)
        self.status_dot.create_oval(2,2,14,14,fill=C["dim"],outline="")
        self.status_lbl=tk.Label(inner,text="Checking...",font=("Segoe UI",14,"bold"),fg=C["text"],bg=C["card"]);self.status_lbl.pack(side=tk.LEFT,padx=8)
        self.detail_lbl=tk.Label(inner,text="",font=("Segoe UI",9),fg=C["dim"],bg=C["card"]);self.detail_lbl.pack(side=tk.LEFT,padx=12)

        # Stats grid
        sf=tk.Frame(self.root,bg=C["bg"]);sf.pack(fill=tk.X,padx=16,pady=(4,0))
        for label,color,key in[("Uptime",C["green"],"uptime"),("Response",C["blue"],"response"),("Checks",C["accent"],"checks"),("SSL Days",C["gold"],"ssl"),("Version",C["purple"],"version")]:
            c=tk.Frame(sf,bg=C["card"],highlightbackground=C["border"],highlightthickness=1);c.pack(side=tk.LEFT,padx=2,fill=tk.X,expand=True,ipady=4)
            tk.Label(c,text=label,font=("Segoe UI",7,"bold"),fg=C["dim"],bg=C["card"]).pack(pady=(4,0))
            lbl=tk.Label(c,text="—",font=("Segoe UI",16,"bold"),fg=color,bg=C["card"]);lbl.pack(pady=(0,4))
            setattr(self,f"stat_{key}",lbl)

        # Chart canvas
        self.chart=tk.Canvas(self.root,bg=C["card"],height=100,highlightthickness=1,highlightbackground=C["border"])
        self.chart.pack(fill=tk.X,padx=16,pady=(4,0))

        # Log area
        tk.Label(self.root,text="EVENT LOG",font=("Segoe UI",9,"bold"),fg=C["dim"],bg=C["bg"]).pack(anchor=tk.W,padx=16,pady=(4,2))
        self.log_text=tk.Text(self.root,bg=C["bg2"],fg=C["text"],font=("Consolas",8),relief=tk.FLAT,borderwidth=0,height=8,state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH,expand=True,padx=16,pady=(0,6))

        tk.Label(self.root,text="Auto-checks every 5s • 24/7 monitoring • Leave open",font=("Segoe UI",7),fg=C["dim"],bg=C["bg"]).pack(side=tk.BOTTOM,pady=4)

    def _start(self):
        self.running=True
        def _loop():
            while self.running:
                try:
                    r=check_page();self.root.after(0,lambda:self._refresh(r))
                except:pass
                time.sleep(CHECK_INTERVAL)
        threading.Thread(target=_loop,daemon=True).start()

    def _refresh(self,r):
        # Status
        if r["online"]:
            self.status_dot.create_oval(2,2,14,14,fill=C["green"],outline="")
            self.status_lbl.config(text="ONLINE",fg=C["green"])
            self.detail_lbl.config(text=f"HTTP {r['status']} • {r['response_ms']}ms • {r['size_kb']}KB")
        else:
            self.status_dot.create_oval(2,2,14,14,fill=C["red"],outline="")
            self.status_lbl.config(text="OFFLINE",fg=C["red"])
            self.detail_lbl.config(text=r["error"][:50])

        # Stats
        log=self.log=load_log()
        self.stat_uptime.config(text=f"{log['uptime_pct']}%")
        self.stat_response.config(text=f"{r.get('response_ms',0)}ms")
        self.stat_checks.config(text=str(log["checks"]))
        self.stat_ssl.config(text=f"{r.get('ssl_days',0)}d")
        self.stat_version.config(text=r.get("version","?")[-8:]if r.get("version")else"?")

        # Chart
        self.chart.delete("all")
        history=log.get("history",[])
        if history:
            w=self.chart.winfo_width()or 600;h=100;step=max(1,w/len(history))
            for i,entry in enumerate(history[-int(w/step):]):
                x=i*step;bar_h=int(h*0.8)if entry["online"]else 2
                color=C["green"]if entry["online"]else C["red"]
                self.chart.create_rectangle(x,h-bar_h,x+step-1,h,fill=color,outline="")

        # Log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END,f"[{datetime.now():%H:%M:%S}] {'✅ ONLINE'if r['online']else'❌ OFFLINE'} "
                            f"HTTP {r.get('status','?')} | {r.get('response_ms',0)}ms | {r.get('size_kb',0)}KB")
        if r.get("content_changed"):self.log_text.insert(tk.END," 🆕 NEW VERSION!")
        if r.get("error"):self.log_text.insert(tk.END,f" — {r['error'][:60]}")
        self.log_text.insert(tk.END,"\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    root=tk.Tk();NexusMonitor(root);root.mainloop()

if __name__=="__main__":main()
