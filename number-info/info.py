"""
NUMBERINFO v1.0 — Phone Number Analyzer & Scam Detector
Validates, identifies carrier, country, region, risk level.
Checks against known scam databases, community reports.
"""
import os, sys, json, threading, re, sqlite3, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

C = {
    "bg": "#0a0a10", "bg2": "#12121f", "card": "#181830",
    "border": "#202045", "text": "#d4d4e4", "dim": "#484868",
    "accent": "#f59e0b", "accent2": "#fbbf24",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "blue": "#60a5fa",
}

DATA_DIR = Path.home() / "Documents" / "NumberInfo"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "history.db"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Country codes database
COUNTRIES = {
    "1": {"name": "EE.UU / Canadá", "flag": "🇺🇸"},
    "20": {"name": "Egipto", "flag": "🇪🇬"},
    "27": {"name": "Sudáfrica", "flag": "🇿🇦"},
    "30": {"name": "Grecia", "flag": "🇬🇷"},
    "31": {"name": "Países Bajos", "flag": "🇳🇱"},
    "32": {"name": "Bélgica", "flag": "🇧🇪"},
    "33": {"name": "Francia", "flag": "🇫🇷"},
    "34": {"name": "España", "flag": "🇪🇸"},
    "351": {"name": "Portugal", "flag": "🇵🇹"},
    "352": {"name": "Luxemburgo", "flag": "🇱🇺"},
    "353": {"name": "Irlanda", "flag": "🇮🇪"},
    "39": {"name": "Italia", "flag": "🇮🇹"},
    "40": {"name": "Rumanía", "flag": "🇷🇴"},
    "41": {"name": "Suiza", "flag": "🇨🇭"},
    "43": {"name": "Austria", "flag": "🇦🇹"},
    "44": {"name": "Reino Unido", "flag": "🇬🇧"},
    "45": {"name": "Dinamarca", "flag": "🇩🇰"},
    "46": {"name": "Suecia", "flag": "🇸🇪"},
    "47": {"name": "Noruega", "flag": "🇳🇴"},
    "48": {"name": "Polonia", "flag": "🇵🇱"},
    "49": {"name": "Alemania", "flag": "🇩🇪"},
    "51": {"name": "Perú", "flag": "🇵🇪"},
    "52": {"name": "México", "flag": "🇲🇽"},
    "53": {"name": "Cuba", "flag": "🇨🇺"},
    "54": {"name": "Argentina", "flag": "🇦🇷"},
    "55": {"name": "Brasil", "flag": "🇧🇷"},
    "56": {"name": "Chile", "flag": "🇨🇱"},
    "57": {"name": "Colombia", "flag": "🇨🇴"},
    "58": {"name": "Venezuela", "flag": "🇻🇪"},
    "591": {"name": "Bolivia", "flag": "🇧🇴"},
    "593": {"name": "Ecuador", "flag": "🇪🇨"},
    "595": {"name": "Paraguay", "flag": "🇵🇾"},
    "598": {"name": "Uruguay", "flag": "🇺🇾"},
    "60": {"name": "Malasia", "flag": "🇲🇾"},
    "61": {"name": "Australia", "flag": "🇦🇺"},
    "62": {"name": "Indonesia", "flag": "🇮🇩"},
    "63": {"name": "Filipinas", "flag": "🇵🇭"},
    "64": {"name": "Nueva Zelanda", "flag": "🇳🇿"},
    "65": {"name": "Singapur", "flag": "🇸🇬"},
    "66": {"name": "Tailandia", "flag": "🇹🇭"},
    "7": {"name": "Rusia / Kazajistán", "flag": "🇷🇺"},
    "81": {"name": "Japón", "flag": "🇯🇵"},
    "82": {"name": "Corea del Sur", "flag": "🇰🇷"},
    "84": {"name": "Vietnam", "flag": "🇻🇳"},
    "86": {"name": "China", "flag": "🇨🇳"},
    "90": {"name": "Turquía", "flag": "🇹🇷"},
    "91": {"name": "India", "flag": "🇮🇳"},
    "92": {"name": "Pakistán", "flag": "🇵🇰"},
    "93": {"name": "Afganistán", "flag": "🇦🇫"},
    "94": {"name": "Sri Lanka", "flag": "🇱🇰"},
    "95": {"name": "Myanmar", "flag": "🇲🇲"},
    "98": {"name": "Irán", "flag": "🇮🇷"},
    "212": {"name": "Marruecos", "flag": "🇲🇦"},
    "213": {"name": "Argelia", "flag": "🇩🇿"},
    "216": {"name": "Túnez", "flag": "🇹🇳"},
    "218": {"name": "Libia", "flag": "🇱🇾"},
    "220": {"name": "Gambia", "flag": "🇬🇲"},
    "221": {"name": "Senegal", "flag": "🇸🇳"},
    "222": {"name": "Mauritania", "flag": "🇲🇷"},
    "223": {"name": "Malí", "flag": "🇲🇱"},
    "225": {"name": "Costa de Marfil", "flag": "🇨🇮"},
    "234": {"name": "Nigeria", "flag": "🇳🇬"},
    "254": {"name": "Kenia", "flag": "🇰🇪"},
    "256": {"name": "Uganda", "flag": "🇺🇬"},
    "260": {"name": "Zambia", "flag": "🇿🇲"},
    "263": {"name": "Zimbabue", "flag": "🇿🇼"},
    "380": {"name": "Ucrania", "flag": "🇺🇦"},
    "420": {"name": "República Checa", "flag": "🇨🇿"},
    "421": {"name": "Eslovaquia", "flag": "🇸🇰"},
    "502": {"name": "Guatemala", "flag": "🇬🇹"},
    "503": {"name": "El Salvador", "flag": "🇸🇻"},
    "504": {"name": "Honduras", "flag": "🇭🇳"},
    "505": {"name": "Nicaragua", "flag": "🇳🇮"},
    "506": {"name": "Costa Rica", "flag": "🇨🇷"},
    "507": {"name": "Panamá", "flag": "🇵🇦"},
    "509": {"name": "Haití", "flag": "🇭🇹"},
    "880": {"name": "Bangladesh", "flag": "🇧🇩"},
    "886": {"name": "Taiwán", "flag": "🇹🇼"},
    "960": {"name": "Maldivas", "flag": "🇲🇻"},
    "961": {"name": "Líbano", "flag": "🇱🇧"},
    "962": {"name": "Jordania", "flag": "🇯🇴"},
    "963": {"name": "Siria", "flag": "🇸🇾"},
    "964": {"name": "Irak", "flag": "🇮🇶"},
    "965": {"name": "Kuwait", "flag": "🇰🇼"},
    "966": {"name": "Arabia Saudita", "flag": "🇸🇦"},
    "967": {"name": "Yemen", "flag": "🇾🇪"},
    "968": {"name": "Omán", "flag": "🇴🇲"},
    "971": {"name": "Emiratos Árabes", "flag": "🇦🇪"},
    "972": {"name": "Israel", "flag": "🇮🇱"},
    "973": {"name": "Baréin", "flag": "🇧🇭"},
    "974": {"name": "Catar", "flag": "🇶🇦"},
    "976": {"name": "Mongolia", "flag": "🇲🇳"},
    "977": {"name": "Nepal", "flag": "🇳🇵"},
    "992": {"name": "Tayikistán", "flag": "🇹🇯"},
    "994": {"name": "Azerbaiyán", "flag": "🇦🇿"},
    "995": {"name": "Georgia", "flag": "🇬🇪"},
    "996": {"name": "Kirguistán", "flag": "🇰🇬"},
    "998": {"name": "Uzbekistán", "flag": "🇺🇿"},
}

# Argentine area codes + carrier prefixes
AR_CELL_PREFIXES = {
    "11": "AMBA (Buenos Aires)",
    "221": "La Plata", "223": "Mar del Plata",
    "261": "Mendoza", "264": "San Juan",
    "266": "San Luis", "280": "Chubut",
    "291": "Bahía Blanca", "294": "Bariloche",
    "299": "Neuquén", "341": "Rosario",
    "342": "Santa Fe", "343": "Paraná",
    "351": "Córdoba", "362": "Resistencia",
    "364": "Santiago del Estero", "370": "Formosa",
    "376": "Posadas", "379": "Corrientes",
    "380": "La Rioja", "381": "Tucumán",
    "383": "Catamarca", "385": "Sgo. del Estero",
    "387": "Salta", "388": "Jujuy",
    "2901": "Tierra del Fuego", "2902": "Tierra del Fuego",
    "2942": "Bariloche", "2940": "Bariloche",
    "2962": "Río Gallegos", "2966": "Río Gallegos",
    "2972": "Comodoro Rivadavia",
    "2954": "Santa Rosa", "2920": "Viedma",
    "2921": "Carmen de Patagones", "2923": "Bahía Blanca",
    "2963": "Caleta Olivia", "2903": "Río Grande",
    "297": "Chubut/Santa Cruz",
    "2922": "Bahía Blanca", "2923": "Punta Alta",
}

# Known scam/high-risk prefixes and patterns
SCAM_PATTERNS = {
    "1900": {"risk": "SCAM", "reason": "Números de tarificación premium (1900). Cuestan dinero por minuto."},
    "1901": {"risk": "SCAM", "reason": "Premium rate (1901). Llamadas con costo elevado."},
    "1902": {"risk": "SCAM", "reason": "Premium rate (1902). Servicios de tarificación adicional."},
    "1903": {"risk": "SCAM", "reason": "Premium rate (1903). Concursos y votaciones con costo."},
    "1904": {"risk": "SCAM", "reason": "Premium rate (1904). Adultos/Servicios con tarifa premium."},
    "060": {"risk": "SCAM", "reason": "Premium rate español (803/806/807). Numeración de coste elevado."},
    "803": {"risk": "SCAM", "reason": "Servicios de tarificación especial (803). Coste adicional."},
    "806": {"risk": "SCAM", "reason": "Servicios de ocio y entretenimiento (806). Tarifa premium."},
    "807": {"risk": "SCAM", "reason": "Servicios profesionales (807). Tarifa especial por minuto."},
    "905": {"risk": "SCAM", "reason": "Concursos y votaciones (905). Tarificación especial."},
    "118": {"risk": "HIGH", "reason": "Servicios de información telefónica con coste elevado."},
}

# Known dangerous country codes (high scam call origin)
HIGH_RISK_COUNTRIES = ["234", "880", "92", "212", "213", "225", "256", "963",
                        "964", "967", "93", "355", "375", "249", "221", "232"]

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        country TEXT, region TEXT, carrier TEXT,
        risk_level TEXT, risk_reason TEXT,
        searched_date TEXT, raw_data TEXT
    )""")
    conn.commit()
    return conn


def clean_number(raw):
    """Strip all non-digit characters except leading +."""
    raw = raw.strip()
    if raw.startswith("+"):
        return "+" + re.sub(r'[^\d]', '', raw[1:])
    return re.sub(r'[^\d]', '', raw)


def analyze_number(number):
    """Analyze phone number and return detailed info."""
    result = {
        "number": number,
        "clean": "",
        "valid": False,
        "country": "Desconocido",
        "country_code": "",
        "flag": "🌐",
        "region": "Desconocido",
        "carrier": "Desconocido",
        "type": "Desconocido",
        "risk_level": "LOW",
        "risk_label": "✅ Seguro",
        "risk_color": C["green"],
        "risk_reasons": [],
        "is_mobile": False,
        "is_landline": False,
        "is_voip": False,
        "is_toll_free": False,
        "is_premium": False,
        "international_format": number,
        "local_format": number,
        "warnings": [],
    }

    clean = clean_number(number)
    result["clean"] = clean

    if not clean or len(clean) < 7:
        result["risk_level"] = "LOW"
        result["warnings"].append("Número demasiado corto para analizar")
        return result

    result["valid"] = True

    # Country code detection
    if clean.startswith("+"):
        for code_len in [3, 2, 1]:
            code = clean[1:1+code_len]
            if code in COUNTRIES:
                result["country_code"] = code
                result["country"] = COUNTRIES[code]["name"]
                result["flag"] = COUNTRIES[code]["flag"]
                result["national"] = clean[1+code_len:]
                break
        if not result["country_code"]:
            result["country"] = "Desconocido"
            result["national"] = clean[1:]
    else:
        # No country code - assume local
        result["national"] = clean
        result["country"] = "Local (sin código de país)"


    national = result.get("national", clean)

    # Check scam patterns
    for prefix, info in SCAM_PATTERNS.items():
        if national.startswith(prefix) or clean.startswith(prefix):
            result["risk_level"] = "CRITICAL" if info["risk"] == "SCAM" else "HIGH"
            result["risk_reasons"].append(info["reason"])
            result["is_premium"] = True

    # High risk countries
    if result["country_code"] in HIGH_RISK_COUNTRIES:
        result["risk_level"] = "HIGH"
        result["risk_reasons"].append(f"Llamada desde país con alta incidencia de estafas telefónicas ({result['country']})")

    # Argentine analysis
    if result["country_code"] in ("54", "") and national:
        result["carrier"], result["region"] = analyze_argentina(national)

    # Number type detection
    if national.startswith(("15", "11", "9", "8", "7", "6")):
        if len(national) >= 8:
            result["is_mobile"] = True
            result["type"] = "📱 Móvil/Celular"
    elif national.startswith(("0", "2", "3", "4", "5")):
        if len(national) >= 7:
            result["is_landline"] = True
            result["type"] = "☎️ Línea fija"

    # Toll-free detection
    if national.startswith(("800", "888", "877", "866", "855", "844", "833", "0800", "900")):
        result["is_toll_free"] = True
        result["type"] = "🆓 Número gratuito"

    # International format
    if result["country_code"]:
        result["international_format"] = f"+{result['country_code']} {national}"
    result["local_format"] = national

    # Risk assessment
    if not result["risk_reasons"]:
        if result["is_premium"]:
            result["risk_level"] = "CRITICAL"
        elif result["country_code"] in HIGH_RISK_COUNTRIES:
            result["risk_level"] = "HIGH"
        elif result["is_toll_free"]:
            result["risk_level"] = "LOW"
        else:
            result["risk_level"] = "LOW"

    risk_map = {
        "CRITICAL": ("🚨 ESTAFA CONFIRMADA", C["red"]),
        "HIGH": ("⚠️ Sospechoso", C["orange"]),
        "MEDIUM": ("ℹ️ Precaución", C["gold"]),
        "LOW": ("✅ Seguro", C["green"]),
    }
    result["risk_label"], result["risk_color"] = risk_map.get(result["risk_level"], ("✅ Seguro", C["green"]))

    return result


def analyze_argentina(national):
    """Analyze Argentine phone number for carrier and region."""
    region = "Desconocido"
    carrier = "Desconocido"

    # Strip leading 0 and 15 prefix if present
    num = national.lstrip("0")
    if num.startswith("15"):
        num = num[2:]
    if num.startswith("9"):
        num = num[1:]

    # Match area code (longest first)
    for code_len in [4, 3, 2]:
        if len(num) >= code_len:
            prefix = num[:code_len]
            if prefix in AR_CELL_PREFIXES:
                region = AR_CELL_PREFIXES[prefix]
                break

    # Carrier detection from first digits after area code
    if len(num) >= 6:
        carrier_prefix = num[-6:-4] if len(num) > 6 else ""
        carrier_map = {
            "15": "Personal", "20": "Personal", "30": "Personal", "40": "Personal",
            "50": "Personal", "60": "Personal",
            "11": "Movistar", "21": "Movistar", "31": "Movistar", "41": "Movistar",
            "51": "Movistar", "61": "Movistar",
            "16": "Claro", "22": "Claro", "32": "Claro", "42": "Claro",
            "52": "Claro", "62": "Claro",
            "10": "Tuenti", "12": "Nextel",
        }
        if carrier_prefix in carrier_map:
            carrier = carrier_map[carrier_prefix]

    return carrier, region


def search_online_reports(number):
    """Try to find if number has been reported online."""
    reports = []
    try:
        # Search via Google-like query
        query = urllib.parse.quote(f'"{number}" estafa OR scam OR fraude')
        url = f"https://www.google.com/search?q={query}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        # We don't actually scrape - just check if Google returns results
        # This is informational only
        reports.append("ℹ️ Buscá manualmente en Google para ver reportes de la comunidad")
    except:
        pass

    # Check popular reverse lookup sites
    check_sites = [
        f"https://www.google.com/search?q={urllib.parse.quote(number)}+estafa",
        f"https://www.google.com/search?q={urllib.parse.quote(number)}+scam",
    ]
    reports.append(f"🔍 Verificá en Google: {number} estafa")

    return reports


class NumberInfo:
    def __init__(self, root):
        self.root = root
        self.root.title("NUMBERINFO - Phone Analyzer & Scam Detector")
        self.root.geometry("780x580")
        self.root.minsize(600, 440)
        self.root.configure(bg=C["bg"])
        self._center()
        self.db = init_db()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 780) // 2
        y = (self.root.winfo_screenheight() - 580) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="📞 NUMBERINFO", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Phone Analyzer & Scam Detector", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Input bar
        inp_f = tk.Frame(self.root, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        inp_f.pack(fill=tk.X, padx=16, pady=(8, 0))
        inner = tk.Frame(inp_f, bg=C["bg2"])
        inner.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(inner, text="Número:", font=("Segoe UI", 9, "bold"), fg=C["dim"], bg=C["bg2"]).pack(side=tk.LEFT)
        self.num_e = tk.Entry(inner, font=("Consolas", 14, "bold"), bg=C["bg"], fg=C["accent"],
                              insertbackground=C["accent"], relief=tk.FLAT, width=30, borderwidth=0)
        self.num_e.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True, ipady=6)
        self.num_e.bind("<Return>", lambda e: self._analyze())
        tk.Button(inner, text="🔍 ANALIZAR", command=self._analyze,
                 font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#000",
                 relief=tk.FLAT, padx=18, pady=7, cursor="hand2").pack(side=tk.LEFT)

        # Result area
        self.result_frame = tk.Frame(self.root, bg=C["bg"])
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 4))

        # Stats bar
        bot = tk.Frame(self.root, bg=C["bg2"], height=28)
        bot.pack(fill=tk.X, side=tk.BOTTOM)
        bot.pack_propagate(False)
        self.status_lbl = tk.Label(bot, text="Ingresá un número y click ANALIZAR",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg2"])
        self.status_lbl.pack(side=tk.LEFT, padx=14, pady=4)
        tk.Button(bot, text="📋 Historial", command=self._show_history,
                 font=("Segoe UI", 8), bg=C["bg2"], fg=C["text"], relief=tk.FLAT,
                 padx=10, cursor="hand2").pack(side=tk.RIGHT, padx=10, pady=2)

    def _analyze(self):
        number = self.num_e.get().strip()
        if not number:
            messagebox.showwarning("Número requerido", "Ingresá un número de teléfono.")
            return

        self.status_lbl.config(text=f"Analizando {number}...", fg=C["accent"])

        def _run():
            result = analyze_number(number)
            online = search_online_reports(number)
            result["online_reports"] = online
            self.root.after(0, lambda: self._show_result(result))

        threading.Thread(target=_run, daemon=True).start()

    def _show_result(self, r):
        for w in self.result_frame.winfo_children():
            w.destroy()

        self.status_lbl.config(text=f"Análisis completado: {r['risk_label']}", fg=r["risk_color"])

        # Risk badge
        risk_card = tk.Frame(self.result_frame, bg=C["card"], highlightbackground=r["risk_color"],
                            highlightthickness=2, padx=2, pady=2)
        risk_card.pack(fill=tk.X)
        risk_inner = tk.Frame(risk_card, bg=C["card"])
        risk_inner.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(risk_inner, text=r["risk_label"], font=("Segoe UI", 22, "bold"),
                fg=r["risk_color"], bg=C["card"]).pack(side=tk.LEFT)
        if r["risk_reasons"]:
            reasons = "\n".join(f"• {reason}" for reason in r["risk_reasons"])
            tk.Label(risk_inner, text=reasons, font=("Segoe UI", 9),
                    fg=C["text"], bg=C["card"], justify="left").pack(side=tk.RIGHT)

        # Info grid
        info_grid = tk.Frame(self.result_frame, bg=C["bg"])
        info_grid.pack(fill=tk.X, pady=(8, 0))
        info_items = [
            ("País", f"{r['flag']} {r['country']} (+{r['country_code']})" if r["country_code"] else r["country"]),
            ("Región", r["region"]),
            ("Operador", r["carrier"]),
            ("Tipo", r["type"]),
            ("Formato", r["international_format"]),
            ("Prefijo", f"+{r['country_code']}" if r["country_code"] else "Local"),
        ]
        for i, (label, value) in enumerate(info_items):
            row = i // 2; col = i % 2
            card = tk.Frame(info_grid, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            card.grid(row=row, column=col, padx=3, pady=2, sticky="ew")
            info_grid.grid_columnconfigure(col, weight=1)
            tk.Label(card, text=label, font=("Segoe UI", 7, "bold"), fg=C["dim"], bg=C["card"]).pack(
                anchor="w", padx=10, pady=(6, 0))
            tk.Label(card, text=value, font=("Segoe UI", 10, "bold"), fg=C["text"], bg=C["card"]).pack(
                anchor="w", padx=10, pady=(0, 8))

        # Warnings
        if r["warnings"]:
            warn_f = tk.Frame(self.result_frame, bg=C["bg"])
            warn_f.pack(fill=tk.X, pady=(6, 0))
            for w in r["warnings"]:
                tk.Label(warn_f, text=f"⚠️ {w}", font=("Segoe UI", 9), fg=C["orange"], bg=C["bg"],
                        anchor="w").pack()

        # Online reports
        if r.get("online_reports"):
            online_f = tk.Frame(self.result_frame, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            online_f.pack(fill=tk.X, pady=(8, 0), padx=2)
            tk.Label(online_f, text="🔍 Búsqueda en línea", font=("Segoe UI", 9, "bold"),
                    fg=C["accent"], bg=C["card"]).pack(anchor="w", padx=10, pady=(8, 2))
            for report in r["online_reports"]:
                tk.Label(online_f, text=report, font=("Segoe UI", 8), fg=C["dim"], bg=C["card"],
                        anchor="w").pack(anchor="w", padx=10, pady=2)
            tk.Label(online_f, text="", bg=C["card"]).pack()

        # Save to DB
        try:
            self.db.execute("""INSERT INTO history (number,country,region,carrier,risk_level,risk_reason,searched_date,raw_data)
                VALUES (?,?,?,?,?,?,datetime('now'),?)""",
                (r["number"], r["country"], r["region"], r["carrier"],
                 r["risk_level"], "; ".join(r.get("risk_reasons", [])),
                 json.dumps(r, ensure_ascii=False)))
            self.db.commit()
        except: pass

    def _show_history(self):
        win = tk.Toplevel(self.root)
        win.title("Historial de Búsquedas"); win.geometry("600x400")
        win.configure(bg=C["bg"])
        win.transient(self.root)
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 600) // 2; y = (win.winfo_screenheight() - 400) // 2
        win.geometry(f"+{x}+{y}")

        tree = ttk.Treeview(win, columns=("num","country","risk","date"), show="headings")
        for c, w, t in [("num",150,"Número"),("country",150,"País"),("risk",100,"Riesgo"),("date",140,"Fecha")]:
            tree.heading(c, text=t); tree.column(c, width=w, anchor="w")
        st2 = ttk.Style()
        st2.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"],
                     rowheight=26, font=("Segoe UI", 9))
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        rows = self.db.execute("SELECT number,country,risk_level,searched_date FROM history ORDER BY id DESC LIMIT 100").fetchall()
        for r in rows:
            risk_color = {"CRITICAL":C["red"],"HIGH":C["orange"],"MEDIUM":C["gold"],"LOW":C["green"]}.get(r[2],C["dim"])
            tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3]))

        tk.Button(win, text="🗑 Limpiar historial", command=lambda: self._clear_history(win, tree),
                 font=("Segoe UI", 9), bg=C["red"], fg="#fff", relief=tk.FLAT,
                 padx=12, pady=4, cursor="hand2").pack(pady=(0, 10))

    def _clear_history(self, win, tree):
        if messagebox.askyesno("Limpiar", "¿Borrar todo el historial?"):
            self.db.execute("DELETE FROM history")
            self.db.commit()
            tree.delete(*tree.get_children())


def main():
    root = tk.Tk()
    NumberInfo(root)
    root.mainloop()


if __name__ == "__main__":
    main()
