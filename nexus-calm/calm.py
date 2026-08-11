"""
NEXUS CALM v1.0 - Anxiety Relief
Breathing exercises, grounding 5-4-3-2-1, affirmations, help.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import math, time, random

C={"bg":"#0d1117","bg2":"#161b22","card":"#1a2332","border":"#253341","text":"#c9d1d9","dim":"#5c6b7a","accent":"#58a6ff","green":"#3fb950","red":"#f85149","purple":"#bc8cff","gold":"#d2991d"}

AFFIRMATIONS=["Estoy a salvo en este momento.","Esta sensacion pasara.","Respira profundamente. Todo esta bien.","Soy fuerte y puedo manejar esto.","Mi cuerpo sabe como calmarse.","Esto es temporal.","No estoy solo/a.","Cada respiracion me trae paz.","Suelto la tension.","Estoy en control de mi respiracion.","Mi mente se aquieta.","El presente es seguro.","Merezco sentirme tranquilo/a.","Inhalo calma, exhalo ansiedad.","Poco a poco, todo vuelve a su lugar."]

BREATHING=[{"name":"4-7-8 (Dr. Weil)","inhale":4,"hold":7,"exhale":8,"desc":"Inhala 4s, retene 7s, exhala 8s. Para dormir."},{"name":"Respiracion en Caja","inhale":4,"hold":4,"exhale":4,"desc":"4-4-4-4. Navy SEALs."},{"name":"Respiracion Profunda","inhale":5,"hold":2,"exhale":6,"desc":"Inhalacion profunda, exhalacion lenta."},{"name":"Exhalacion Extendida","inhale":2,"hold":0,"exhale":4,"desc":"Exhalar el doble. Activa sistema parasimpatico."}]

GROUNDING=[("5 cosas que VES","Mira a tu alrededor. Nombra 5 cosas que puedas ver."),("4 cosas que TOCAS","Senti 4 texturas diferentes a tu alcance."),("3 cosas que OYES","Escucha atentamente. Nombra 3 sonidos."),("2 cosas que HUELES","Huele 2 cosas cercanas."),("1 cosa que SABOREAS","Siente el sabor en tu boca o toma agua.")]

HELP_LINES=["Argentina: 135 (Linea de Prevencion del Suicidio)","Argentina: 0800-345-1435 (Salud Mental)","Mexico: 800-911-2000 (Linea de la Vida)","Espana: 024 (Linea de Atencion Suicida)","Colombia: 106 (Linea de Salud Mental)","Chile: *4141 (No estas solo)","Peru: 113 (Salud Mental)","Uruguay: 0800-0767 (Linea Vida)","EEUU: 988 (Suicide Lifeline)","Internacional: befrienders.org","Recuerda: La ansiedad es tratable. Busca ayuda profesional.","No estas solo/a. Hay personas que te quieren ayudar."]

class App:
    def __init__(self,root):
        self.root=root;root.title("NEXUS CALM");root.geometry("720x580");root.minsize(500,400);root.configure(bg=C["bg"])
        root.update_idletasks();x=(root.winfo_screenwidth()-720)//2;y=(root.winfo_screenheight()-580)//2;root.geometry(f"+{x}+{y}")
        self._build()

    def _build(self):
        tk.Label(self.root,text="🧘 NEXUS CALM — Alivio de Ansiedad",font=("Segoe UI",16,"bold"),fg=C["green"],bg=C["bg"]).pack(pady=(14,4))
        nb=ttk.Notebook(self.root);nb.pack(fill=tk.BOTH,expand=True,padx=14,pady=6)
        st=ttk.Style();st.theme_use("clam");st.configure("TNotebook",background=C["bg"],borderwidth=0);st.configure("TNotebook.Tab",background=C["bg2"],foreground=C["dim"],padding=[10,5],font=("Segoe UI",10));st.map("TNotebook.Tab",background=[("selected",C["bg"])],foreground=[("selected",C["accent"])])
        self._tab_breath(nb);self._tab_ground(nb);self._tab_affirm(nb);self._tab_help(nb)
        tk.Label(self.root,text="💙 La ansiedad es tratable. No estas solo/a.",font=("Segoe UI",8),fg=C["dim"],bg=C["bg"]).pack(side=tk.BOTTOM,pady=6)

    def _tab_breath(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="🫁 Respiracion")
        self.bc=tk.Canvas(t,bg=C["bg"],height=220,highlightthickness=0);self.bc.pack(fill=tk.X,padx=20,pady=(14,0))
        self.bc.create_text(360,110,text="Presiona INICIAR",font=("Segoe UI",14),fill=C["dim"])
        ctrl=tk.Frame(t,bg=C["bg"]);ctrl.pack(fill=tk.X,padx=20,pady=6)
        self.bv=tk.StringVar(value=BREATHING[0]["name"])
        ttk.Combobox(ctrl,textvariable=self.bv,values=[b["name"]for b in BREATHING],state="readonly",font=("Segoe UI",10),width=22).pack(side=tk.LEFT)
        self.bb=tk.Button(ctrl,text="▶ INICIAR",command=self._toggle_b,font=("Segoe UI",10,"bold"),bg=C["accent"],fg="#fff",relief=tk.FLAT,padx=14,pady=5,cursor="hand2");self.bb.pack(side=tk.LEFT,padx=6)
        self.br=False;self.bp="";self.brd=60;self.bt=0
        ti=tk.Frame(t,bg=C["card"],highlightbackground=C["border"],highlightthickness=1);ti.pack(fill=tk.X,padx=20,pady=4,ipady=4)
        self.bi=tk.Label(ti,text="Selecciona un ejercicio y presiona INICIAR",font=("Segoe UI",9),fg=C["dim"],bg=C["card"]);self.bi.pack(padx=12,pady=4)

    def _toggle_b(self):
        if self.br:self.br=False;self.bb.config(text="▶ INICIAR",bg=C["accent"],fg="#fff");self.bc.delete("all");self.bc.create_text(360,110,text="Presiona INICIAR",font=("Segoe UI",14),fill=C["dim"]);return
        self.br=True;self.bb.config(text="⏹ DETENER",bg=C["red"],fg="#fff")
        for b in BREATHING:
            if b["name"]==self.bv.get():self.be=b;break
        self.bp="inhale";self.bt=0;self.brd=60;self.bi.config(text=self.be["desc"]);self._anim_b()

    def _anim_b(self):
        if not self.br:return
        e=self.be;c=self.bc;c.delete("all");w=c.winfo_width()or 680;cx,cy=w//2,110;m=45;M=125
        if self.bp=="inhale":self.bt+=0.05;p=min(self.bt/e["inhale"],1);self.brd=m+(M-m)*p;cl=C["green"];ins="INHALA";cd=max(0,int(e["inhale"]-self.bt)+1)
        elif self.bp=="hold":self.bt+=0.05;p=min(self.bt/e["hold"],1);self.brd=M;cl=C["gold"];ins="RETENE";cd=max(0,int(e["hold"]-self.bt)+1)
        elif self.bp=="exhale":self.bt+=0.05;p=min(self.bt/e["exhale"],1);self.brd=M-(M-m)*p;cl=C["accent"];ins="EXHALA";cd=max(0,int(e["exhale"]-self.bt)+1)
        else:self.brd=m;cl=C["accent"];ins="...";cd=0
        if self.bp=="inhale"and p>=1:self.bp="hold"if e["hold"]>0 else"exhale";self.bt=0
        elif self.bp=="hold"and p>=1:self.bp="exhale";self.bt=0
        elif self.bp=="exhale"and p>=1:self.bp="inhale";self.bt=0
        r=int(self.brd*(1+math.sin(time.time()*3)*0.03))
        for i in range(3,0,-1):c.create_oval(cx-r-i*6,cy-r-i*6,cx+r+i*6,cy+r+i*6,outline="",fill="#{:02x}{:02x}{:02x}".format(int(cl[1:3],16),int(cl[3:5],16),int(cl[5:7],16)))
        c.create_text(cx,cy-10,text=ins,font=("Segoe UI",18,"bold"),fill="#fff")
        if cd>0:c.create_text(cx,cy+18,text=str(cd),font=("Segoe UI",24,"bold"),fill=cl)
        self.root.after(50,self._anim_b)

    def _tab_ground(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="🧠 Grounding");self.gs=0
        self.gl=tk.Label(t,text="Tecnica 5-4-3-2-1\n\nPresiona SIGUIENTE",font=("Segoe UI",13),fg=C["dim"],bg=C["bg"],justify="center");self.gl.pack(expand=True,pady=16)
        self.gd=tk.Label(t,text="",font=("Segoe UI",10),fg=C["accent"],bg=C["bg"],wraplength=500,justify="center");self.gd.pack()
        bf=tk.Frame(t,bg=C["bg"]);bf.pack(pady=14)
        tk.Button(bf,text="▶ SIGUIENTE",command=self._next_g,font=("Segoe UI",11,"bold"),bg=C["purple"],fg="#fff",relief=tk.FLAT,padx=18,pady=5,cursor="hand2").pack(side=tk.LEFT,padx=3)
        tk.Button(bf,text="↺ Reiniciar",command=self._reset_g,font=("Segoe UI",9),bg=C["bg2"],fg=C["text"],relief=tk.FLAT,padx=10,pady=4,cursor="hand2").pack(side=tk.LEFT,padx=3)

    def _next_g(self):
        if self.gs>=len(GROUNDING):self.gl.config(text="✅ Completado!\n\nRespira hondo. Ya pasaste los 5 pasos.",fg=C["green"]);self.gd.config(text="Repeti cuando lo necesites.");self.gs=0;return
        t,d=GROUNDING[self.gs];self.gl.config(text=t,fg=C["purple"]);self.gd.config(text=d);self.gs+=1

    def _reset_g(self):self.gs=0;self.gl.config(text="Tecnica 5-4-3-2-1\n\nPresiona SIGUIENTE",fg=C["dim"]);self.gd.config(text="")

    def _tab_affirm(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="💭 Afirmaciones")
        self.al=tk.Label(t,text="Presiona NUEVA para una afirmacion positiva",font=("Segoe UI",13),fg=C["dim"],bg=C["bg"],wraplength=500,justify="center");self.al.pack(expand=True,pady=16)
        tk.Button(t,text="✨ NUEVA AFIRMACION",command=self._new_aff,font=("Segoe UI",11,"bold"),bg=C["accent"],fg="#fff",relief=tk.FLAT,padx=18,pady=6,cursor="hand2").pack()

    def _new_aff(self):self.al.config(text=random.choice(AFFIRMATIONS),fg=C["green"])

    def _tab_help(self,nb):
        t=tk.Frame(nb,bg=C["bg"]);nb.add(t,text="🆘 Ayuda")
        tk.Label(t,text="Lineas de ayuda - 24/7 - Gratis",font=("Segoe UI",12,"bold"),fg=C["accent"],bg=C["bg"]).pack(pady=(12,6))
        for line in HELP_LINES:
            tk.Label(t,text=f"  • {line}",font=("Segoe UI",9),fg=C["text"],bg=C["bg"],anchor="w",wraplength=600,justify="left").pack(fill=tk.X,padx=20,pady=1)


def main():
    root=tk.Tk();App(root);root.mainloop()

if __name__=="__main__":main()
