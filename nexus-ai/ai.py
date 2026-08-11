"""
NEXUS AI v1.0 — Local AI Chat Assistant
Connects to Ollama for local LLM. Works offline.
Precise, accurate responses. No API keys needed.
"""
import os, sys, json, threading, time, re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, font as tkfont

try: import requests; HAS_REQ = True
except: HAS_REQ = False

C = {
    "bg": "#0a0a12", "bg2": "#121222", "card": "#1a1a35",
    "border": "#1e1e42", "text": "#d0d0e4", "dim": "#484870",
    "accent": "#8b5cf6", "accent2": "#a78bfa",
    "user_msg": "#1a3a5c", "ai_msg": "#1a2a1a",
    "green": "#34d399", "red": "#f87171", "blue": "#60a5fa",
    "code_bg": "#0d0d1a",
}

DATA_DIR = Path.home() / "Documents" / "NexusAI"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "chat_history.json"

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
SYSTEM_PROMPT = """Eres un asistente AI preciso y util. Responde de forma:
1. PRECISA: Da informacion exacta, verificable.
2. CONCISA: Ve al punto sin rodeos.
3. UTIL: Ofrece soluciones practicas.
4. HONESTA: Si no sabes algo, dilo claramente.
Responde en espanol. Si escriben codigo, usa markdown."""


def check_ollama():
    """Check if Ollama is running and list available models."""
    if not HAS_REQ: return False, []
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
    except: pass
    return False, []


def query_ollama(model, messages, stream=False):
    """Send chat request to Ollama API."""
    if not HAS_REQ: return "Error: requests library not installed"
    try:
        payload = {"model": model, "messages": messages, "stream": stream,
                    "options": {"temperature": 0.7, "num_predict": 1024}}
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            return data.get("message", {}).get("content", "No response")
        return f"Error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Connection error: {str(e)[:100]}\n\nAsegurate de que Ollama este corriendo.\nEjecuta: ollama serve"


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages[-200:], f, ensure_ascii=False)


class NexusAI:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS AI — Local Assistant")
        self.root.geometry("820x600")
        self.root.minsize(550, 400)
        self.root.configure(bg=C["bg"])
        self._center()

        self.ollama_available, self.models = check_ollama()
        self.current_model = self.models[0] if self.models else DEFAULT_MODEL
        self.messages = load_history()
        if not self.messages:
            self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        self._build()
        self._load_chat()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 820) // 2
        y = (self.root.winfo_screenheight() - 600) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=14, pady=(10, 0))
        tk.Label(hdr, text="🤖 NEXUS AI", font=("Segoe UI", 16, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)

        # Model selector
        right_f = tk.Frame(hdr, bg=C["bg"]); right_f.pack(side=tk.RIGHT)
        if self.ollama_available and self.models:
            self.model_var = tk.StringVar(value=self.current_model)
            cb = ttk.Combobox(right_f, textvariable=self.model_var, values=self.models,
                             state="readonly", font=("Segoe UI", 9), width=15)
            cb.pack(side=tk.LEFT, padx=4)
            cb.bind("<<ComboboxSelected>>", lambda e: setattr(self, "current_model", self.model_var.get()))
            tk.Label(right_f, text="🟢 Ollama", font=("Segoe UI", 8, "bold"),
                    fg=C["green"], bg=C["bg"]).pack(side=tk.LEFT)
        else:
            tk.Label(right_f, text="🔴 Offline — Instala Ollama para AI", font=("Segoe UI", 8, "bold"),
                    fg=C["red"], bg=C["bg"]).pack(side=tk.RIGHT)
            tk.Button(right_f, text="?", font=("Segoe UI", 8), bg=C["bg2"], fg=C["accent"],
                     relief=tk.FLAT, padx=6, cursor="hand2",
                     command=lambda: messagebox.showinfo("Setup",
                         "1. Descarga Ollama: https://ollama.com\n"
                         "2. Instala y ejecuta: ollama serve\n"
                         "3. Descarga un modelo: ollama pull llama3.2\n"
                         "4. Reinicia Nexus AI")).pack(side=tk.RIGHT, padx=4)

        # Chat area
        self.chat_frame = tk.Frame(self.root, bg=C["bg"])
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 0))

        self.chat_canvas = tk.Canvas(self.chat_frame, bg=C["bg"], highlightthickness=0)
        self.chat_scroll = ttk.Scrollbar(self.chat_frame, command=self.chat_canvas.yview)
        self.msg_frame = tk.Frame(self.chat_canvas, bg=C["bg"])
        self.msg_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(
            scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.create_window((0, 0), window=self.msg_frame, anchor="nw", width=780)
        self.chat_canvas.configure(yscrollcommand=self.chat_scroll.set)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Input bar
        inp_f = tk.Frame(self.root, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        inp_f.pack(fill=tk.X, padx=14, pady=6)
        inner = tk.Frame(inp_f, bg=C["bg2"]); inner.pack(fill=tk.X, padx=8, pady=6)
        self.input_e = tk.Text(inner, font=("Segoe UI", 10), bg=C["bg"], fg=C["text"],
                               insertbackground=C["accent"], relief=tk.FLAT, height=2,
                               wrap=tk.WORD, borderwidth=0)
        self.input_e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.input_e.bind("<Return>", self._send)
        self.input_e.bind("<Shift-Return>", lambda e: None)

        tk.Button(inner, text="▶", command=self._send, font=("Segoe UI", 12, "bold"),
                 bg=C["accent"], fg="#fff", relief=tk.FLAT, padx=12, cursor="hand2").pack(side=tk.RIGHT)

        # Bottom bar
        bot = tk.Frame(self.root, bg=C["bg"], height=24); bot.pack(fill=tk.X, side=tk.BOTTOM)
        bot.pack_propagate(False)
        tk.Button(bot, text="🗑 Clear Chat", command=self._clear_chat, font=("Segoe UI", 8),
                 bg=C["red"], fg="#fff", relief=tk.FLAT, padx=8, cursor="hand2").pack(side=tk.RIGHT, padx=10, pady=2)
        self.status_lbl = tk.Label(bot, text="Ready", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.LEFT, padx=10, pady=2)

    def _send(self, event=None):
        if isinstance(event, tk.Event) and event.state & 1:  # Shift+Enter = newline
            return
        if isinstance(event, tk.Event):
            return "break"

        text = self.input_e.get(1.0, tk.END).strip()
        if not text: return "break" if event else None

        self.input_e.delete(1.0, tk.END)
        self._add_message("user", text)
        self.input_e.config(state=tk.DISABLED)
        self.status_lbl.config(text="🤖 Thinking...", fg=C["accent"])

        def _run():
            self.messages.append({"role": "user", "content": text})
            if self.ollama_available:
                response = query_ollama(self.current_model, self.messages)
            else:
                response = self._offline_response(text)

            self.messages.append({"role": "assistant", "content": response})
            save_history(self.messages)
            self.root.after(0, lambda: self._add_message("ai", response))
            self.root.after(0, lambda: self.status_lbl.config(text="Ready", fg=C["dim"]))
            self.root.after(0, lambda: self.input_e.config(state=tk.NORMAL))
            self.root.after(100, lambda: self.input_e.focus())

        threading.Thread(target=_run, daemon=True).start()
        return "break" if event else None

    def _offline_response(self, text):
        """Basic offline responses for common questions."""
        t = text.lower()
        if "hola" in t or "hello" in t:
            return "¡Hola! Soy Nexus AI. Actualmente estoy en modo offline. Instala Ollama (https://ollama.com) para activar el modo AI completo con respuestas precisas.\n\nMientras tanto, puedo ayudarte con:\n• Preguntas basicas\n• Informacion sobre Nexus Tools\n• Comandos y codigo simple"
        if "nexus" in t or "tools" in t or "app" in t:
            return "Nexus Tools es un ecosistema de 28 aplicaciones gratuitas para Windows y Android. Incluye escaneres de seguridad, limpiadores de PC, VPN, TV en vivo, dashboards, herramientas de desarrollo y mas.\n\nTodas las apps son 100% gratis, sin publicidad y de codigo abierto.\n\nDescargalas en: https://gonzalitodev.github.io/h4ck3r-zone/websecurity-landing/"
        if "ollama" in t:
            return "Para instalar Ollama:\n\n1. Ve a https://ollama.com\n2. Descarga el instalador para Windows\n3. Ejecuta 'ollama serve' en una terminal\n4. Descarga un modelo: 'ollama pull llama3.2'\n5. Reinicia Nexus AI\n\nUna vez instalado, este chat usara IA local 100% gratis y offline."
        if "codigo" in t or "python" in t or "program" in t:
            return "Puedo ayudarte con codigo cuando tengas Ollama instalado. Mientras tanto, puedo escribir ejemplos basicos:\n\n```python\n# Hola Mundo en Python\nprint('Hola Mundo')\n\n# Funcion simple\ndef suma(a, b):\n    return a + b\n```"
        if "?" in t or "como" in t or "que" in t:
            return "Buena pregunta. Para respuestas mas precisas y detalladas, necesito estar conectado a un modelo de IA local (Ollama).\n\nInstala Ollama gratis desde https://ollama.com y reinicia esta app para activar el modo AI completo.\n\nCon Ollama instalado, podre:\n• Responder preguntas tecnicas con precision\n• Escribir y explicar codigo\n• Analizar problemas\n• Dar respuestas detalladas y verificables"
        return f"No tengo acceso a mi modelo de IA en este momento. Para activar respuestas precisas y completas:\n\n1. Instala Ollama: https://ollama.com\n2. Ejecuta: ollama pull llama3.2\n3. Reinicia Nexus AI\n\nMientras tanto, preguntame sobre Nexus Tools o temas basicos."

    def _add_message(self, role, text):
        is_user = role == "user"
        bg_color = C["user_msg"] if is_user else C["ai_msg"]
        label_text = "TÚ" if is_user else "🤖 NEXUS AI"

        msg_frame = tk.Frame(self.msg_frame, bg=C["bg"])
        msg_frame.pack(fill=tk.X, pady=4, padx=4)

        # Header
        header = tk.Frame(msg_frame, bg=C["bg"]); header.pack(anchor="w" if not is_user else "e")
        tk.Label(header, text=label_text, font=("Segoe UI", 8, "bold"),
                fg=C["accent"], bg=C["bg"]).pack(side=tk.LEFT if not is_user else tk.RIGHT)

        # Content card
        card = tk.Frame(msg_frame, bg=bg_color, highlightbackground=C["border"], highlightthickness=1)
        card.pack(anchor="w" if not is_user else "e", padx=20, fill=tk.X)

        # Check for code blocks
        parts = re.split(r'(```[\s\S]*?```)', text)
        for part in parts:
            if part.startswith("```"):
                code = part[3:-3].strip()
                if "\n" in code:
                    code = code.split("\n", 1)[1] if code.startswith("\n") or not code[0].isalpha() else code
                code_frame = tk.Frame(card, bg=C["code_bg"])
                code_frame.pack(fill=tk.X, padx=8, pady=4)
                code_label = tk.Label(code_frame, text=code, font=("Consolas", 9),
                                     fg=C["green"], bg=C["code_bg"], anchor="w", justify="left",
                                     wraplength=650)
                code_label.pack(padx=8, pady=6)
            elif part.strip():
                tk.Label(card, text=part.strip(), font=("Segoe UI", 10),
                        fg=C["text"], bg=bg_color, anchor="w", justify="left",
                        wraplength=650).pack(anchor="w", padx=12, pady=(8, 0))

        # Copy button (AI messages only)
        if not is_user:
            copy_f = tk.Frame(card, bg=bg_color); copy_f.pack(fill=tk.X)
            tk.Label(copy_f, text="📋 Copy", font=("Segoe UI", 7), fg=C["dim"], bg=bg_color,
                    cursor="hand2").pack(side=tk.RIGHT, padx=8, pady=(0, 6))
            copy_f.winfo_children()[0].bind("<Button-1>", lambda e, t=text: self._copy(t))

        tk.Label(msg_frame, text="", bg=C["bg"]).pack()  # spacer
        self._scroll_bottom()

    def _copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _load_chat(self):
        for msg in self.messages[1:]:  # Skip system prompt
            role = msg.get("role", "user")
            if role in ("user", "assistant"):
                self._add_message("user" if role == "user" else "ai", msg["content"])

    def _clear_chat(self):
        if messagebox.askyesno("Clear", "Delete entire chat history?"):
            self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            save_history(self.messages)
            for w in self.msg_frame.winfo_children():
                w.destroy()

    def _scroll_bottom(self):
        self.root.after(100, lambda: self.chat_canvas.yview_moveto(1.0))


def main():
    root = tk.Tk()
    NexusAI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
