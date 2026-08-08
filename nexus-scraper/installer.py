"""Nexus Data Scraper - Installer"""
import os, sys, shutil, subprocess, tempfile
from pathlib import Path; import tkinter as tk
from tkinter import ttk, messagebox; import ctypes
APP_EXE="NexusScraper.exe";APP_NAME="Nexus Data Scraper"
def is_admin():
    try:return ctypes.windll.shell32.IsUserAnAdmin()
    except:return False
def shortcuts(idir):
    vbs=f'''Set W=CreateObject("WScript.Shell"):Set F=CreateObject("Scripting.FileSystemObject")
d=W.SpecialFolders("Desktop"):s=W.SpecialFolders("StartMenu"):p=s&"\\Programs\\Nexus Scraper"
Set sc=W.CreateShortcut(d&"\\Nexus Scraper.lnk"):sc.TargetPath="{idir}\\{APP_EXE}"
sc.WorkingDirectory="{idir}":sc.IconLocation="shell32.dll,23":sc.Save
If Not F.FolderExists(p)Then F.CreateFolder(p)
Set sc2=W.CreateShortcut(p&"\\Nexus Scraper.lnk"):sc2.TargetPath="{idir}\\{APP_EXE}"
sc2.WorkingDirectory="{idir}":sc2.IconLocation="shell32.dll,23":sc2.Save'''
    vp=os.path.join(tempfile.gettempdir(),"ns.vbs")
    with open(vp,"w")as f:f.write(vbs)
    subprocess.run(["cscript","//nologo",vp],capture_output=True)
    try:os.remove(vp)
    except:pass
def reg(idir):
    for c in[["reg","add",r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NexusScraper","/v","DisplayName","/d",APP_NAME,"/f"],
             ["reg","add",r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NexusScraper","/v","UninstallString","/d",f'cmd /c rmdir /s /q "{idir}" & reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\NexusScraper" /f',"/f"],
             ["reg","add",r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NexusScraper","/v","DisplayIcon","/d",f'{idir}\\{APP_EXE}',"/f"],
             ["reg","add",r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NexusScraper","/v","DisplayVersion","/d","1.0","/f"]]:
        subprocess.run(c,capture_output=True)
class SW:
    def __init__(self,r,s,d):
        self.root=r;self.src=s;self.idir=d
        r.title(f"{APP_NAME} - Setup");r.geometry("480x320")
        r.configure(bg="#0a080f");r.resizable(False,False)
        r.update_idletasks();x=(r.winfo_screenwidth()-480)//2;y=(r.winfo_screenheight()-320)//2;r.geometry(f"+{x}+{y}")
        tk.Label(r,text="🕷️ "+APP_NAME,font=("Segoe UI",16,"bold"),fg="#c084fc",bg="#0a080f").pack(pady=(24,4))
        tk.Label(r,text="Web Data Extraction Tool",font=("Segoe UI",10),fg="#585070",bg="#0a080f").pack()
        info=tk.Frame(r,bg="#1a1530",highlightbackground="#2a2050",highlightthickness=1)
        info.pack(fill=tk.X,padx=30,pady=14,ipadx=10,ipady=8)
        tk.Label(info,text=f"Install: {d}",font=("Consolas",9),fg="#d8d4e8",bg="#1a1530").pack(anchor="w",padx=10)
        self.p=ttk.Progressbar(r,mode="indeterminate",length=340);self.p.pack(pady=(6,6))
        self.t=tk.Label(r,text="Ready",font=("Segoe UI",9),fg="#585070",bg="#0a080f");self.t.pack()
        bf=tk.Frame(r,bg="#0a080f");bf.pack(pady=(12,10))
        self.ib=tk.Button(bf,text="🕷️ INSTALL",command=self._i,font=("Segoe UI",11,"bold"),bg="#a855f7",fg="#fff",relief=tk.FLAT,padx=28,pady=8,cursor="hand2")
        self.ib.pack(side=tk.LEFT,padx=4)
        self.lb=tk.Button(bf,text="▶ Launch",command=self._l,font=("Segoe UI",11,"bold"),bg="#34d399",fg="#000",relief=tk.FLAT,padx=22,pady=8,cursor="hand2",state=tk.DISABLED)
        self.lb.pack(side=tk.LEFT,padx=4)
    def _i(self):
        self.ib.config(state=tk.DISABLED,text="Installing...");self.p.start(10);self.root.update()
        try:
            os.makedirs(self.idir,exist_ok=True)
            shutil.copy2(str(self.src),os.path.join(self.idir,APP_EXE))
            self.t.config(text="Shortcuts...",fg="#c084fc");self.root.update()
            shortcuts(self.idir);reg(self.idir)
            self.p.stop();self.t.config(text="Done!",fg="#34d399")
            self.ib.config(text="✓ Installed",bg="#34d399");self.lb.config(state=tk.NORMAL)
        except Exception as e:self.p.stop();self.t.config(text=str(e)[:80],fg="#f87171");messagebox.showerror("Error",str(e))
    def _l(self):subprocess.Popen([os.path.join(self.idir,APP_EXE)]);self.root.destroy()
def main():
    if getattr(sys,'frozen',False):b=Path(sys._MEIPASS)if hasattr(sys,'_MEIPASS')else Path(sys.executable).parent
    else:b=Path(__file__).parent/"dist"
    src=b/APP_EXE
    if not src.exists():src=Path(__file__).parent.parent/"dist"/APP_EXE
    if not src.exists():r=tk.Tk();r.withdraw();messagebox.showerror("Error","App not found");return
    admin=is_admin()
    d=os.path.join(os.environ["ProgramFiles"],"Nexus Scraper")if admin else os.path.join(os.environ["LOCALAPPDATA"],"Nexus Scraper")
    r=tk.Tk();SW(r,src,d);r.mainloop()
if __name__=="__main__":main()
