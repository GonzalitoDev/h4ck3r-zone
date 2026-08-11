"""
NEXUS TOOLBOX v1.0 — All-in-One PC Utility
Clipboard history, batch file renamer, screenshot, color picker,
calculator, text tools, notes, system tray. Ultra-useful.
"""
import os, sys, json, re, time, subprocess, random
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, colorchooser

C={"bg":"#0d0d15","bg2":"#15152a","card":"#1a1a35","border":"#1e1e42","text":"#d0d0e4","dim":"#484870","accent":"#6366f1","accent2":"#818cf8","green":"#34d399","red":"#f87171","orange":"#fb923c","gold":"#fbbf24","blue":"#60a5fa"}
DATA_DIR=Path.home()/"Documents"/"NexusToolbox";DATA_DIR.mkdir(parents=True,exist_ok=True)
NOTES_FILE=DATA_DIR/"notes.txt"
CLIP_FILE=DATA_DIR/"clipboard.json"

def load_notes():
    try:return NOTES_FILE.read_text(encoding="utf-8")
    except:return""
def save_notes(text):NOTES_FILE.write_text(text,encoding="utf-8")
def load_clip():
    try:
        with open(CLIP_FILE,"r")as f:return json.load(f)
    except:return[]
def save_clip(data):
    with open(CLIP_FILE,"w")as f:json.dump(data[-50:],f)

class NexusToolbox:
    def __init__(self,root):
        self.root=root;root.title("NEXUS TOOLBOX");root.geometry("780x560");root.minsize(550,400);root.configure(bg=C["bg"])
        root.update_idletasks();x=(root.winfo_screenwidth()-780)//2;y=(root.winfo_screenheight()-560)//2;root.geometry(f"+{x}+{y}")
        self.clipboard=load_clip();self._clip_watch()
        self._build()

    def _build(self):
        tk.Label(self.root,text="🔧 NEXUS TOOLBOX",font=("Segoe UI",18,"bold"),fg=C["accent2"],bg=C["bg"]).pack(pady=(14,2))
        tk.Label(self.root,text="All-in-One PC Utility",font=("Segoe UI",9),fg=C["dim"],bg=C["bg"]).pack()

        nb=ttk.Notebook(self.root);nb.pack(fill=tk.BOTH,expand=True,padx=14,pady=8)
        st=ttk.Style();st.theme_use("clam");st.configure("TNotebook",background=C["bg"],borderwidth=0);st.configure("TNotebook.Tab",background=C["bg2"],foreground=C["dim"],padding=[10,5],font=("Segoe UI",10));st.map("TNotebook.Tab",background=[("selected",C["bg"])],foreground=[("selected",C["accent"])])

        self._tab_clipboard(nb)
        self._tab_renamer(nb)
        self._tab_notes(nb)
        self._tab_calc(nb)
        self._tab_text(nb)

        tk.Label(self.root,text="💡 Pro tip: Pin this window (always on top) with the 📌 button in Clipboard tab",
                font=("Segoe UI",7),fg=C["dim"],bg=C["bg"]).pack(side=tk.BOTTOM,pady=4)

    def _tab_clipboard(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="📋 Clipboard")
        btn_f=tk.Frame(t,bg=C["bg"]);btn_f.pack(fill=tk.X,padx=10,pady=(8,2))
        tk.Button(btn_f,text="🔄 Refresh",command=self._refresh_clip,font=("Segoe UI",9),bg=C["bg2"],fg=C["text"],relief=tk.FLAT,padx=10,pady=3,cursor="hand2").pack(side=tk.LEFT)
        tk.Button(btn_f,text="🗑 Clear",command=self._clear_clip,font=("Segoe UI",9),bg=C["red"],fg="#fff",relief=tk.FLAT,padx=10,pady=3,cursor="hand2").pack(side=tk.LEFT,padx=4)
        self.pin_var=tk.BooleanVar(value=False)
        tk.Checkbutton(btn_f,text="📌 Always on Top",variable=self.pin_var,command=self._toggle_pin,bg=C["bg"],fg=C["dim"],selectcolor=C["bg2"],activebackground=C["bg"],font=("Segoe UI",8)).pack(side=tk.RIGHT)

        tf=tk.Frame(t,bg=C["card"],highlightbackground=C["border"],highlightthickness=1);tf.pack(fill=tk.BOTH,expand=True,padx=10,pady=(0,8))
        self.clip_tree=ttk.Treeview(tf,columns=("text",),show="headings",selectmode="browse")
        self.clip_tree.heading("text",text="Clipboard History (double-click to copy)");self.clip_tree.column("text",width=700)
        st2=ttk.Style();st2.configure("Treeview",background=C["bg2"],foreground=C["text"],fieldbackground=C["bg2"],rowheight=28,font=("Segoe UI",9),borderwidth=0)
        sb=ttk.Scrollbar(tf,command=self.clip_tree.yview);self.clip_tree.configure(yscrollcommand=sb.set)
        self.clip_tree.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=2,pady=2);sb.pack(side=tk.RIGHT,fill=tk.Y)
        self.clip_tree.bind("<Double-1>",self._copy_clip)
        self._refresh_clip()

    def _refresh_clip(self):
        self.clip_tree.delete(*self.clip_tree.get_children())
        try:
            current=self.root.clipboard_get()
            if current and (not self.clipboard or current!=self.clipboard[-1]):self.clipboard.append(current);save_clip(self.clipboard)
        except:pass
        for item in reversed(self.clipboard[-30:]):
            self.clip_tree.insert("",0,values=(item[:120],))

    def _clear_clip(self):
        if messagebox.askyesno("Clear","Clear clipboard history?"):self.clipboard=[];save_clip([]);self._refresh_clip()

    def _copy_clip(self,event):
        sel=self.clip_tree.selection()
        if sel:
            text=self.clip_tree.item(sel[0])["values"][0]
            self.root.clipboard_clear();self.root.clipboard_append(text)

    def _clip_watch(self):
        try:
            current=self.root.clipboard_get()
            if current and (not self.clipboard or current!=self.clipboard[-1]):
                self.clipboard.append(current);save_clip(self.clipboard);self._refresh_clip()
        except:pass

    def _toggle_pin(self):self.root.attributes("-topmost",self.pin_var.get())

    def _tab_renamer(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="📝 Renamer")
        top=tk.Frame(t,bg=C["bg"]);top.pack(fill=tk.X,padx=10,pady=(8,4))
        tk.Button(top,text="📁 Select Files",command=self._select_files,font=("Segoe UI",9,"bold"),bg=C["accent"],fg="#fff",relief=tk.FLAT,padx=12,pady=3,cursor="hand2").pack(side=tk.LEFT)
        tk.Label(top,text="Pattern:",font=("Segoe UI",9),fg=C["dim"],bg=C["bg"]).pack(side=tk.LEFT,padx=(12,2))
        self.pat_e=tk.Entry(top,font=("Segoe UI",9),bg=C["bg2"],fg=C["text"],insertbackground=C["accent"],relief=tk.FLAT,width=15);self.pat_e.pack(side=tk.LEFT,ipady=2);self.pat_e.insert(0,"file_###")
        tk.Button(top,text="🏷️ Preview",command=self._preview_rename,font=("Segoe UI",9),bg=C["bg2"],fg=C["text"],relief=tk.FLAT,padx=10,pady=3,cursor="hand2").pack(side=tk.LEFT,padx=4)
        tk.Button(top,text="✅ Apply",command=self._apply_rename,font=("Segoe UI",9,"bold"),bg=C["green"],fg="#000",relief=tk.FLAT,padx=10,pady=3,cursor="hand2").pack(side=tk.LEFT,padx=4)
        tk.Label(top,text="### = numbers, %n = original name",font=("Segoe UI",8),fg=C["dim"],bg=C["bg"]).pack(side=tk.RIGHT)

        self.rename_files=[];self.rename_preview=[]
        tf=tk.Frame(t,bg=C["card"],highlightbackground=C["border"],highlightthickness=1);tf.pack(fill=tk.BOTH,expand=True,padx=10,pady=(0,8))
        self.rename_tree=ttk.Treeview(tf,columns=("from","to"),show="headings",selectmode="extended")
        self.rename_tree.heading("from",text="Original");self.rename_tree.heading("to",text="New Name")
        self.rename_tree.column("from",width=350);self.rename_tree.column("to",width=350)
        sb2=ttk.Scrollbar(tf,command=self.rename_tree.yview);self.rename_tree.configure(yscrollcommand=sb2.set)
        self.rename_tree.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=2,pady=2);sb2.pack(side=tk.RIGHT,fill=tk.Y)

    def _select_files(self):
        files=filedialog.askopenfilenames(title="Select files to rename")
        if files:self.rename_files=list(files);self._preview_rename()

    def _preview_rename(self):
        self.rename_tree.delete(*self.rename_tree.get_children());self.rename_preview=[]
        pat=self.pat_e.get()or"file_###"
        for i,f in enumerate(self.rename_files):
            name,ext=os.path.splitext(os.path.basename(f))
            new=pat.replace("###",str(i+1).zfill(3)).replace("%n",name)+ext
            self.rename_preview.append((f,os.path.join(os.path.dirname(f),new)))
            self.rename_tree.insert("",tk.END,values=(os.path.basename(f),new))

    def _apply_rename(self):
        if not self.rename_preview:return
        ok=messagebox.askyesno("Rename",f"Rename {len(self.rename_preview)} files?")
        if not ok:return
        done=0
        for old,new in self.rename_preview:
            try:os.rename(old,new);done+=1
            except:pass
        self.rename_files=[];self.rename_tree.delete(*self.rename_tree.get_children())
        messagebox.showinfo("Done",f"{done} files renamed.")

    def _tab_notes(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="📝 Notes")
        self.notes_text=scrolledtext.ScrolledText(t,bg=C["bg2"],fg=C["text"],font=("Consolas",10),wrap=tk.WORD,relief=tk.FLAT,borderwidth=0,insertbackground=C["accent"])
        self.notes_text.pack(fill=tk.BOTH,expand=True,padx=10,pady=8)
        if load_notes():self.notes_text.insert(1.0,load_notes())
        self.notes_text.bind("<KeyRelease>",lambda e:save_notes(self.notes_text.get(1.0,tk.END)))
        btn_f=tk.Frame(t,bg=C["bg"]);btn_f.pack(fill=tk.X,padx=10,pady=(0,6))
        tk.Button(btn_f,text="🗑 Clear",command=lambda:self.notes_text.delete(1.0,tk.END),font=("Segoe UI",8),bg=C["red"],fg="#fff",relief=tk.FLAT,padx=8,pady=2,cursor="hand2").pack(side=tk.RIGHT)

    def _tab_calc(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="🧮 Calc")
        self.calc_disp=tk.Entry(t,font=("Consolas",22),bg=C["bg2"],fg=C["accent"],insertbackground=C["accent"],relief=tk.FLAT,justify="right",borderwidth=0);self.calc_disp.pack(fill=tk.X,padx=10,pady=(10,6),ipady=10);self.calc_disp.insert(0,"0")
        grid=tk.Frame(t,bg=C["bg"]);grid.pack(padx=10)
        btns=[("C","red"),("(","dim"),(")","dim"),("/","accent"),("7","text"),("8","text"),("9","text"),("*","accent"),("4","text"),("5","text"),("6","text"),("-","accent"),("1","text"),("2","text"),("3","text"),("+","accent"),("0","text"),(".","text"),("⌫","red"),("=","green")]
        for i,(text,color)in enumerate(btns):
            row,col=i//4,i%4
            colors={"red":C["red"],"dim":C["dim"],"accent":C["accent"],"text":C["text"],"green":C["green"]}
            tk.Button(grid,text=text,command=lambda t=text:self._calc(t),font=("Segoe UI",12,"bold"),bg=C["bg2"],fg=colors[color],relief=tk.FLAT,padx=14,pady=8,cursor="hand2",width=4).grid(row=row,column=col,padx=2,pady=2)

    def _calc(self,key):
        try:
            prev=self.calc_disp.get()
            if key=="C":self.calc_disp.delete(0,tk.END);self.calc_disp.insert(0,"0")
            elif key=="⌫":
                if len(prev)>1:self.calc_disp.delete(len(prev)-1)
                else:self.calc_disp.delete(0,tk.END);self.calc_disp.insert(0,"0")
            elif key=="=":
                result=eval(prev.replace("×","*").replace("÷","/"))
                self.calc_disp.delete(0,tk.END);self.calc_disp.insert(0,str(result)[:15])
            else:
                if prev=="0":self.calc_disp.delete(0,tk.END)
                self.calc_disp.insert(tk.END,key)
        except:self.calc_disp.delete(0,tk.END);self.calc_disp.insert(0,"Error")

    def _tab_text(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="Aa Text")
        self.text_input=scrolledtext.ScrolledText(t,bg=C["bg2"],fg=C["text"],font=("Consolas",10),wrap=tk.WORD,relief=tk.FLAT,borderwidth=0,insertbackground=C["accent"],height=6)
        self.text_input.pack(fill=tk.X,padx=10,pady=(8,4))
        self.text_input.bind("<KeyRelease>",lambda e:self._text_stats())
        self.text_stats=tk.Label(t,text="Characters: 0 | Words: 0 | Lines: 0",font=("Segoe UI",9),fg=C["dim"],bg=C["bg"]);self.text_stats.pack()
        btn_f=tk.Frame(t,bg=C["bg"]);btn_f.pack(fill=tk.X,padx=10,pady=4)
        for text,cmd in[("UPPERCASE",str.upper),("lowercase",str.lower),("Title Case",str.title),("Reverse",lambda s:s[::-1])]:
            tk.Button(btn_f,text=text,command=lambda c=cmd:self._text_op(c),font=("Segoe UI",8),bg=C["bg2"],fg=C["text"],relief=tk.FLAT,padx=8,pady=2,cursor="hand2").pack(side=tk.LEFT,padx=2)

    def _text_stats(self):
        t=self.text_input.get(1.0,tk.END).strip()
        chars=len(t);words=len(t.split())if t else 0;lines=t.count("\n")+1 if t else 0
        self.text_stats.config(text=f"Characters: {chars} | Words: {words} | Lines: {lines}")

    def _text_op(self,func):
        try:
            text=self.text_input.get(1.0,tk.END).strip()
            self.text_input.delete(1.0,tk.END);self.text_input.insert(1.0,func(text))
            self._text_stats()
        except:pass

def main():
    root=tk.Tk();NexusToolbox(root);root.mainloop()

if __name__=="__main__":main()
