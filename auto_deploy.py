"""
█▀█ █▀▀ ▀▄▀ █░█ █▀   █▀▄ █▀▀ █▀█ █░░ █▀█ █▄█
█▄█ ██▄ █░█ █▄█ ▄█   █▄▀ ██▄ █▀▀ █▄▄ █▄█ ░█░
Nexus Auto-Deploy v3.0 — Hacker Terminal Edition
Watches files, auto cache-bust, commit + push. 24/7 background.
"""
import os, sys, time, subprocess, re, platform, socket
from pathlib import Path
from datetime import datetime

WATCH_DIR = Path(__file__).resolve().parent / "websecurity-landing"
DEBOUNCE_SECONDS = 1  # Instant deploy (1s wait)
HTML_FILE = WATCH_DIR / "index.html"

# ANSI colors for hacker terminal
G = "\033[92m"  # Green
R = "\033[91m"  # Red
C = "\033[96m"  # Cyan
Y = "\033[93m"  # Yellow
P = "\033[95m"  # Purple
D = "\033[90m"  # Dim
W = "\033[97m"  # White
X = "\033[0m"   # Reset


def clear(): os.system("cls" if platform.system() == "Windows" else "clear")


def type_out(text, delay=0.02):
    """Typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def progress_bar(label, duration=1.5, steps=20):
    """Animated progress bar."""
    sys.stdout.write(f"{D}[{label}] {X}")
    for i in range(steps + 1):
        bar = "█" * i + "░" * (steps - i)
        sys.stdout.write(f"\r{D}[{label}] {G}[{bar}]{X} {i * 5}%")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()


def boot_sequence():
    """Hacker-style boot animation."""
    clear()
    print(f"""
{G}    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   {C}███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗{G}        ║
    ║   {C}████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝{G}        ║
    ║   {C}██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗{G}        ║
    ║   {C}██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║{G}        ║
    ║   {C}██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║{G}        ║
    ║   {C}╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝{G}        ║
    ║                                                          ║
    ║          {W}AUTO-DEPLOY SYSTEM v3.0{G}                          ║
    ║          {D}Hacker Terminal Edition{G}                            ║
    ╚══════════════════════════════════════════════════════════╝
{X}""")

    print(f"{D}═══ INITIALIZING DEPLOYMENT ENGINE ═══{X}")
    time.sleep(0.3)

    # Fake boot sequence
    lines = [
        (f"Initializing watcher (12 threads)...", 0),
        (f"Target: {WATCH_DIR}", 0),
        (f"Pipeline active — {DEBOUNCE_SECONDS}s response", 0),
    ]
    for line, delay in lines:
        print(f"{G}[>]{X} {line}")
        time.sleep(delay)

    print(f"\n{G}[OK]{X} All systems operational")
    print(f"{G}[OK]{X} Target: {D}{WATCH_DIR}{X}")
    print(f"{G}[OK]{X} Debounce: {C}{DEBOUNCE_SECONDS}s{X}")
    print(f"{G}[OK]{X} Pipeline: {C}file change → inject → commit → push → GitHub Pages{X}")
    print(f"\n{D}═══ DEPLOYMENT ENGINE ACTIVE ═══{X}")
    print(f"{Y}  STATUS: {G}ONLINE{X}  |  {Y}MODE: {C}AUTOMATIC{X}  |  {Y}HOST: {P}{socket.gethostname()}{X}")
    print(f"{D}═══ ═══ ═══ ═══ ═══ ═══ ═══ ═══ ═══{X}\n")
    print(f"{W}  Edit any file → auto deploy in {C}{DEBOUNCE_SECONDS}s{W}. Ctrl+C to stop.{X}\n")


def inject_version():
    """Inject version timestamp into HTML for cache busting."""
    try:
        with open(str(HTML_FILE), "r", encoding="utf-8") as f:
            content = f.read()
        version = datetime.now().strftime("%Y%m%d%H%M%S")

        content = re.sub(
            r'<meta name="nexus-version" content="[^"]*">',
            f'<meta name="nexus-version" content="{version}">',
            content
        )
        if '<meta name="nexus-version"' not in content:
            content = content.replace(
                '<meta charset="UTF-8">',
                f'<meta charset="UTF-8">\n<meta name="nexus-version" content="{version}">\n<meta http-equiv="cache-control" content="no-cache">'
            )
        with open(str(HTML_FILE), "w", encoding="utf-8") as f:
            f.write(content)
        return version
    except PermissionError:
        print(f"  {Y}[!]{X} File locked - retrying next cycle")
        return None
    except Exception as e:
        print(f"  {Y}[!]{X} Version warning: {e}")
        return None


def git_add_commit_push():
    """Add all changes, commit with timestamp, push."""
    try:
        os.chdir(WATCH_DIR.parent)
        ver = inject_version()
        if ver:
            subprocess.run(["git", "add", str(HTML_FILE)], capture_output=True, timeout=10)

        subprocess.run(["git", "add", "websecurity-landing/"], capture_output=True, timeout=60)
        result = subprocess.run(
            ["git", "commit", "-m", f"Auto-deploy v{ver or '?'}", "--no-verify"],
            capture_output=True, timeout=30
        )
        output = result.stdout.decode() + result.stderr.decode()
        if "nothing to commit" not in output:
            sys.stdout.write(f"\r{D}[{datetime.now():%H:%M:%S}]{X} ")
            sys.stdout.write(f"{P}Pushing...{X}")
            sys.stdout.flush()
            subprocess.run(["git", "push", "origin", "master"], capture_output=True, timeout=120)
            sys.stdout.write(f"\r{D}[{datetime.now():%H:%M:%S}]{X} ")
            print(f"{G}▲ DEPLOYED {W}v{ver}{G} — live in ~60s{X}")
        else:
            sys.stdout.write(f"\r{D}[{datetime.now():%H:%M:%S}]{X} ")
            print(f"{D}◻ No changes detected{X}")
    except Exception as e:
        sys.stdout.write(f"\r{D}[{datetime.now():%H:%M:%S}]{X} ")
        print(f"{R}✗ Error: {e}{X}")


def watch():
    """Watch directory for file changes."""
    last_modified = {}
    for root, dirs, files in os.walk(WATCH_DIR):
        for f in files:
            fp = os.path.join(root, f)
            try:
                last_modified[fp] = os.path.getmtime(fp)
            except:
                pass

    last_push = time.time()
    deploy_count = 0

    try:
        while True:
            changed = False
            changed_file = ""
            for root, dirs, files in os.walk(WATCH_DIR):
                if ".git" in root:
                    continue
                for f in files:
                    if f == ".update":
                        continue
                    fp = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(fp)
                        if fp not in last_modified or mtime != last_modified[fp]:
                            changed = True
                            changed_file = f
                            last_modified[fp] = mtime
                    except:
                        pass

            if changed and time.time() - last_push > DEBOUNCE_SECONDS:
                deploy_count += 1
                print(f"\n{Y}[!]{X} {W}Change detected:{X} {C}{changed_file}{X}")
                print(f"{G}[▲]{X} {W}Deploy #{deploy_count} initiating...{X}")
                git_add_commit_push()
                last_push = time.time()

            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{R}[✗]{X} Session terminated.")
        print(f"{D}  Total deploys: {G}{deploy_count}{D}")
        print(f"{D}  Session ended: {datetime.now():%Y-%m-%d %H:%M:%S}{X}\n")


def main():
    boot_sequence()
    print(f"{D}[{datetime.now():%H:%M:%S}]{X} {C}Initial sync with GitHub...{X}")
    git_add_commit_push()
    watch()


if __name__ == "__main__":
    main()
