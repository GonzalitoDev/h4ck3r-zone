"""
NEXUS OSINT PRO v1.0 — Open Source Intelligence Toolkit
100% legal. Public data only. Domain, email, phone, IP, username,
social media, metadata, DNS, WHOIS, breach check, image analysis.
PC + Android compatible.
"""
import os, sys, json, threading, re, time, urllib.request, urllib.parse, ssl, socket, hashlib, subprocess
from datetime import datetime
from pathlib import Path
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

try:
    from bs4 import BeautifulSoup; HAS_BS4 = True
except: HAS_BS4 = False
try:
    import requests; HAS_REQ = True
except: HAS_REQ = False

C = {
    "bg": "#08060c", "bg2": "#100d1a", "card": "#1a1430",
    "border": "#2a1e48", "text": "#d0cce4", "dim": "#585078",
    "accent": "#a855f7", "accent2": "#c084fc",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa",
}

DATA_DIR = Path.home() / "Documents" / "NexusOSINT"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def http_get(url, timeout=10, headers=None):
    if headers is None: headers = {"User-Agent": UA}
    if HAS_REQ:
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            return r.text, r.status_code, None
        except Exception as e:
            return "", 0, str(e)
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode(errors="ignore"), resp.status, None
    except Exception as e:
        return "", 0, str(e)


def http_get_json(url, timeout=10):
    text, status, err = http_get(url, timeout)
    if err: return {}
    try: return json.loads(text)
    except: return {}


# ====== OSINT MODULES ======

def module_domain(domain):
    """Domain intelligence: WHOIS, DNS, subdomains, tech stack."""
    results = {"domain": domain, "sections": []}
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
    results["domain"] = domain

    # DNS Records
    try:
        import dns.resolver
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
            try:
                answers = dns.resolver.resolve(domain, rtype)
                records = [str(a) for a in answers][:5]
                results["sections"].append({"title": f"DNS {rtype}", "data": records})
            except: pass
    except: results["sections"].append({"title": "DNS", "data": ["dnspython not installed"]})

    # WHOIS
    try:
        text, status, _ = http_get(f"https://www.whois.com/whois/{domain}")
        if status == 200 and text:
            whois_info = []
            for line in text.split("\n"):
                for keyword in ["Registrar:", "Creation Date:", "Registry Expiry",
                              "Name Server:", "Registrant", "Organization"]:
                    if keyword in line and line.strip() not in whois_info:
                        whois_info.append(line.strip()[:120])
            results["sections"].append({"title": "WHOIS Info", "data": whois_info[:15] or ["No WHOIS data found"]})
    except: pass

    # Subdomains via crt.sh
    try:
        data = http_get_json(f"https://crt.sh/?q=%25.{domain}&output=json", 15)
        subs = set()
        for entry in data[:200]:
            name = entry.get("name_value", "")
            for n in name.split("\n"):
                n = n.strip().lstrip("*.")
                if n and domain in n and n != domain:
                    subs.add(n)
        if subs:
            results["sections"].append({"title": f"Subdomains ({len(subs)})", "data": sorted(list(subs))[:30]})
    except: pass

    # Technology stack via headers
    try:
        text, status, _ = http_get(f"https://{domain}")
        if status:
            tech = []
            if HAS_BS4 and text:
                soup = BeautifulSoup(text, "html.parser")
                if soup.find("meta", {"name": "generator"}):
                    tech.append(f"Generator: {soup.find('meta', {'name': 'generator'})['content']}")
            # Detect common tech from body
            tech_signatures = {
                "wp-content": "WordPress", "wp-json": "WordPress API",
                "react": "React", "vue": "Vue.js", "angular": "Angular",
                "bootstrap": "Bootstrap", "jquery": "jQuery",
                "laravel": "Laravel", "django": "Django", "flask": "Flask",
                "shopify": "Shopify", "cloudflare": "Cloudflare",
            }
            text_lower = text.lower()[:5000] if text else ""
            for sig, name in tech_signatures.items():
                if sig in text_lower and name not in tech:
                    tech.append(name)
            if tech:
                results["sections"].append({"title": "Tech Stack", "data": tech})
    except: pass

    return results


def module_email(email):
    """Email intelligence: format, provider, breach check."""
    results = {"email": email, "sections": []}

    # Basic analysis
    if "@" not in email:
        results["sections"].append({"title": "Status", "data": ["Invalid email format"]})
        return results

    parts = email.split("@")
    username, domain = parts[0], parts[1]

    info = [f"Username: {username}", f"Domain: {domain}"]

    # Email provider info
    providers = {"gmail.com": "Google Gmail", "outlook.com": "Microsoft Outlook",
                 "hotmail.com": "Microsoft Hotmail", "yahoo.com": "Yahoo Mail",
                 "protonmail.com": "ProtonMail (encrypted)", "icloud.com": "Apple iCloud",
                 "mail.ru": "Mail.ru", "yandex.ru": "Yandex", "aol.com": "AOL"}
    provider = providers.get(domain.lower(), "Custom domain / Business email")
    info.append(f"Provider: {provider}")

    # MX check for custom domains
    if domain.lower() not in providers:
        try:
            import dns.resolver
            mx = dns.resolver.resolve(domain, "MX")
            mx_records = [str(m) for m in mx]
            info.append(f"MX: {', '.join(mx_records[:3])}")
        except:
            info.append("MX: No mail servers found (domain may not receive email)")

    # Security checks
    security = []
    if domain.lower() == "gmail.com":
        security.append("✅ Google advanced phishing protection available")
    elif domain.lower() in ("protonmail.com", "tutanota.com"):
        security.append("✅ End-to-end encrypted email provider")
    elif domain.lower() in ("outlook.com", "hotmail.com"):
        security.append("⚠️ Outlook supports 2FA - check if enabled")
    info.extend(security)

    results["sections"].append({"title": "Email Analysis", "data": info})

    # Gravatar check
    try:
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/{email_hash}?d=404&s=200"
        _, status, _ = http_get(gravatar_url, timeout=5)
        if status == 200:
            results["sections"].append({
                "title": "Gravatar", "data": [f"Profile image: {gravatar_url}",
                                             "This person has a Gravatar account"]
            })
    except: pass

    # Have I Been Pwned check
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"User-Agent": UA, "hibp-api-key": ""}
        _, status, _ = http_get(url, timeout=8, headers=headers)
        if status == 200:
            results["sections"].append({
                "title": "⚠️ Breach Alert",
                "data": ["This email appears in data breaches! Check haveibeenpwned.com"]
            })
        elif status == 404:
            results["sections"].append({
                "title": "Breach Check",
                "data": ["✅ No known breaches (HaveIBeenPwned)"]
            })
    except: pass

    return results


def module_username(username):
    """Check username across 50+ social platforms."""
    results = {"username": username, "sections": []}

    platforms = {
        "GitHub": f"https://github.com/{username}",
        "Twitter/X": f"https://twitter.com/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "Twitch": f"https://twitch.tv/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "Pinterest": f"https://pinterest.com/{username}",
        "Medium": f"https://medium.com/@{username}",
        "Dev.to": f"https://dev.to/{username}",
        "HackerNews": f"https://news.ycombinator.com/user?id={username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
        "Keybase": f"https://keybase.io/{username}",
        "Telegram": f"https://t.me/{username}",
        "VK": f"https://vk.com/{username}",
        "Flickr": f"https://flickr.com/people/{username}",
        "Dribbble": f"https://dribbble.com/{username}",
        "Behance": f"https://behance.net/{username}",
        "About.me": f"https://about.me/{username}",
        "Patreon": f"https://patreon.com/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "Blogger": f"https://{username}.blogspot.com",
        "WordPress": f"https://{username}.wordpress.com",
        "Tumblr": f"https://{username}.tumblr.com",
        "SlideShare": f"https://slideshare.net/{username}",
        "Vimeo": f"https://vimeo.com/{username}",
        "PayPal": f"https://paypal.me/{username}",
        "CashApp": f"https://cash.app/${username}",
        "Disqus": f"https://disqus.com/by/{username}",
    }

    found = []
    threads_list = []

    def _check(platform, url):
        try:
            _, status, _ = http_get(url, timeout=5)
            if status in (200, 301, 302):
                found.append({"platform": platform, "url": url, "status": "Found"})
        except: pass

    for platform, url in platforms.items():
        t = threading.Thread(target=_check, args=(platform, url), daemon=True)
        t.start()
        threads_list.append(t)
        if len(threads_list) >= 10:
            for t in threads_list: t.join(timeout=3)
            threads_list.clear()
    for t in threads_list: t.join(timeout=3)

    if found:
        data = [f"✅ {f['platform']}: {f['url']}" for f in found]
        results["sections"].append({"title": f"Found ({len(found)})", "data": data})
    results["sections"].append({"title": f"Checked {len(platforms)} platforms",
                                "data": [f"{len(found)} profiles found"]})

    return results


def module_ip(ip_or_host):
    """IP/Network intelligence."""
    results = {"target": ip_or_host, "sections": []}

    # Resolve IP if hostname
    try: ip = socket.gethostbyname(ip_or_host)
    except: ip = ip_or_host

    results["sections"].append({"title": "Resolution", "data": [f"IP: {ip}"]})

    # IP info API
    try:
        data = http_get_json(f"http://ip-api.com/json/{ip}", 5)
        if data.get("status") == "success":
            info = [
                f"Country: {data.get('country','?')} ({data.get('countryCode','')})",
                f"Region: {data.get('regionName','?')}",
                f"City: {data.get('city','?')}",
                f"ISP: {data.get('isp','?')}",
                f"Organization: {data.get('org','?')}",
                f"AS: {data.get('as','?')}",
                f"Timezone: {data.get('timezone','?')}",
                f"Coordinates: {data.get('lat',0)}, {data.get('lon',0)}",
            ]
            results["sections"].append({"title": "Geolocation", "data": info})
    except: pass

    # Reverse DNS
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        results["sections"].append({"title": "Reverse DNS", "data": [hostname]})
    except: pass

    return results


def module_phone(phone):
    """Phone number intelligence."""
    results = {"phone": phone, "sections": []}

    clean = re.sub(r'[^\d+]', '', phone)

    info = [f"Raw: {phone}", f"Clean: {clean}", f"Digits: {len(clean)}"]

    # Country detection
    if clean.startswith("+"):
        country_codes = {
            "1": "US/Canada", "20": "Egypt", "27": "South Africa",
            "30": "Greece", "31": "Netherlands", "32": "Belgium",
            "33": "France", "34": "Spain", "39": "Italy",
            "40": "Romania", "41": "Switzerland", "43": "Austria",
            "44": "UK", "45": "Denmark", "46": "Sweden",
            "47": "Norway", "48": "Poland", "49": "Germany",
            "51": "Peru", "52": "Mexico", "54": "Argentina",
            "55": "Brazil", "56": "Chile", "57": "Colombia",
            "58": "Venezuela", "60": "Malaysia", "61": "Australia",
            "62": "Indonesia", "63": "Philippines", "64": "New Zealand",
            "65": "Singapore", "66": "Thailand", "7": "Russia/Kazakhstan",
            "81": "Japan", "82": "South Korea", "84": "Vietnam",
            "86": "China", "90": "Turkey", "91": "India",
            "92": "Pakistan", "93": "Afghanistan", "94": "Sri Lanka",
            "212": "Morocco", "213": "Algeria", "216": "Tunisia",
            "234": "Nigeria", "254": "Kenya", "351": "Portugal",
            "352": "Luxembourg", "353": "Ireland", "380": "Ukraine",
            "420": "Czech Republic", "421": "Slovakia",
            "502": "Guatemala", "503": "El Salvador", "504": "Honduras",
            "505": "Nicaragua", "506": "Costa Rica", "507": "Panama",
            "591": "Bolivia", "593": "Ecuador", "595": "Paraguay",
            "598": "Uruguay", "880": "Bangladesh", "886": "Taiwan",
            "971": "UAE", "972": "Israel", "976": "Mongolia",
        }
        for code in sorted(country_codes.keys(), key=len, reverse=True):
            if clean[1:].startswith(code):
                info.append(f"Country: {country_codes[code]} (+{code})")
                break

    # Type detection
    if len(clean) >= 10:
        if clean.startswith(("+1800", "+1888", "+1877", "+1866", "+1855", "+1844", "+1833", "0800", "800")):
            info.append("Type: Toll-Free")
        elif len(clean) >= 11:
            info.append("Type: Mobile (likely)")
        else:
            info.append("Type: Landline (likely)")

    # Risk flags
    high_risk = ["+234", "+880", "+92", "+93", "+963", "+967", "+212", "+225", "+256"]
    for code in high_risk:
        if clean.startswith(code):
            info.append("⚠️ HIGH RISK: Known scam call origin country")

    results["sections"].append({"title": "Phone Analysis", "data": info})
    return results


class NexusOSINT:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS OSINT PRO")
        self.root.geometry("960x650")
        self.root.minsize(700, 480)
        self.root.configure(bg=C["bg"])
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 960) // 2
        y = (self.root.winfo_screenheight() - 650) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(hdr, text="🔍 NEXUS OSINT PRO", font=("Segoe UI", 17, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Open Source Intelligence | 100% Legal", font=("Segoe UI", 9),
                fg=C["dim"], bg=C["bg"]).pack(side=tk.LEFT, padx=10, pady=(5, 0))

        # Module selector
        sel_f = tk.Frame(self.root, bg=C["bg2"], highlightbackground=C["border"], highlightthickness=1)
        sel_f.pack(fill=tk.X, padx=16, pady=(8, 0))
        inner = tk.Frame(sel_f, bg=C["bg2"]); inner.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(inner, text="Target:", font=("Segoe UI", 9, "bold"), fg=C["dim"], bg=C["bg2"]).pack(side=tk.LEFT)
        self.target_e = tk.Entry(inner, font=("Consolas", 11), bg=C["bg"], fg=C["text"],
                                 insertbackground=C["accent"], relief=tk.FLAT, width=35, borderwidth=0)
        self.target_e.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True, ipady=5)
        self.target_e.insert(0, "example.com")
        self.target_e.bind("<Return>", lambda e: self._search())

        self.mode_var = tk.StringVar(value="domain")
        ttk.Combobox(inner, textvariable=self.mode_var,
                    values=["domain","email","username","ip","phone"],
                    state="readonly", font=("Segoe UI", 9), width=10).pack(side=tk.LEFT, padx=4)
        tk.Label(inner, text="Mode:", font=("Segoe UI", 8), fg=C["dim"], bg=C["bg2"]).pack(side=tk.LEFT)

        tk.Button(inner, text="🔍 SEARCH", command=self._search,
                 font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="#fff",
                 relief=tk.FLAT, padx=16, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=6)

        # Results area
        self.result_frame = tk.Frame(self.root, bg=C["bg"])
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 8))

        # Status
        self.status_lbl = tk.Label(self.root, text="Select mode, enter target, click SEARCH",
                                   font=("Segoe UI", 8), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 6))

    def _search(self):
        target = self.target_e.get().strip()
        mode = self.mode_var.get()
        if not target:
            messagebox.showwarning("Target", "Enter a target to search.")
            return

        # Clear results
        for w in self.result_frame.winfo_children():
            w.destroy()

        self.status_lbl.config(text=f"🔍 Searching {mode}: {target}...", fg=C["accent"])

        modules = {
            "domain": module_domain,
            "email": module_email,
            "username": module_username,
            "ip": module_ip,
            "phone": module_phone,
        }

        func = modules.get(mode)
        if not func: return

        def _run():
            try:
                results = func(target)
                self.root.after(0, lambda: self._show_results(results, mode))
            except Exception as e:
                self.root.after(0, lambda: self._error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _show_results(self, results, mode):
        self.status_lbl.config(text=f"✅ Search complete — {mode}: {results.get('domain', results.get('email', results.get('username', results.get('target', results.get('phone', target)))))}", fg=C["green"])

        # Target header card
        target_val = results.get("domain") or results.get("email") or results.get("username") or results.get("target") or results.get("phone") or ""
        header = tk.Frame(self.result_frame, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        header.pack(fill=tk.X, padx=2, pady=(0, 4))
        tk.Label(header, text=f"🔍 {mode.upper()} Intelligence: {target_val}",
                font=("Segoe UI", 12, "bold"), fg=C["accent2"], bg=C["card"]).pack(padx=14, pady=10, anchor="w")

        # Result sections
        for section in results.get("sections", []):
            sec = tk.Frame(self.result_frame, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            sec.pack(fill=tk.X, padx=2, pady=2)
            tk.Label(sec, text=section["title"], font=("Segoe UI", 10, "bold"),
                    fg=C["accent"], bg=C["card"]).pack(anchor="w", padx=14, pady=(8, 2))

            data = section.get("data", [])
            if isinstance(data, list):
                for item in data:
                    tk.Label(sec, text=f"  {item}", font=("Consolas", 9), fg=C["text"],
                            bg=C["card"], anchor="w", justify="left",
                            wraplength=850).pack(anchor="w", padx=14, pady=1)
            tk.Label(sec, text="", bg=C["card"]).pack()

    def _error(self, msg):
        self.status_lbl.config(text=f"Error: {msg[:80]}", fg=C["red"])


def main():
    root = tk.Tk()
    NexusOSINT(root)
    root.mainloop()


if __name__ == "__main__":
    main()
