"""
Nexus Auto-Deploy v2.0 — Watch files, auto cache-bust, commit + push.
Runs in background. Injects version timestamp for instant updates.
"""
import os, sys, time, subprocess, re
from pathlib import Path
from datetime import datetime

WATCH_DIR = Path(__file__).resolve().parent / "websecurity-landing"
DEBOUNCE_SECONDS = 3  # Wait 3s after last change
HTML_FILE = WATCH_DIR / "index.html"


def inject_version():
    """Inject version timestamp into HTML for cache busting."""
    try:
        # Use raw file operations for Windows compatibility
        with open(str(HTML_FILE), "r", encoding="utf-8") as f:
            content = f.read()
        version = datetime.now().strftime("%Y%m%d%H%M%S")

        # Remove old version
        content = re.sub(
            r'<meta name="nexus-version" content="[^"]*">',
            f'<meta name="nexus-version" content="{version}">',
            content
        )

        # If version meta doesn't exist, add it after charset
        if '<meta name="nexus-version"' not in content:
            content = content.replace(
                '<meta charset="UTF-8">',
                f'<meta charset="UTF-8">\n<meta name="nexus-version" content="{version}">\n<meta http-equiv="cache-control" content="no-cache">'
            )

        with open(str(HTML_FILE), "w", encoding="utf-8") as f:
            f.write(content)
        return version
    except PermissionError:
        print(f"  ⚠️ File locked - retrying on next cycle")
        return None
    except Exception as e:
        print(f"  Version inject warning: {e}")
        return None


def git_add_commit_push():
    """Add all changes, commit with timestamp, push."""
    try:
        os.chdir(WATCH_DIR.parent)

        # Inject version for cache busting
        ver = inject_version()
        if ver:
            subprocess.run(["git", "add", str(HTML_FILE)], capture_output=True, timeout=5)

        subprocess.run(["git", "add", "websecurity-landing/"], capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "commit", "-m", f"Auto-deploy v{ver or '?'}", "--no-verify"],
            capture_output=True, timeout=10
        )
        output = result.stdout.decode() + result.stderr.decode()
        if "nothing to commit" not in output:
            subprocess.run(["git", "push", "origin", "master"], capture_output=True, timeout=30)
            print(f"[{datetime.now():%H:%M:%S}] ✓ Pushed v{ver} — page updates in 1-3 min")
        else:
            print(f"[{datetime.now():%H:%M:%S}] No changes")
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] ✗ Error: {e}")


def watch():
    """Watch directory for file changes."""
    print(f"👀 Watching: {WATCH_DIR}")
    print("   Edit any file → auto commit + push in {DEBOUNCE_SECONDS}s")
    print("   Press Ctrl+C to stop\n")

    last_modified = {}
    for root, dirs, files in os.walk(WATCH_DIR):
        for f in files:
            fp = os.path.join(root, f)
            try:
                last_modified[fp] = os.path.getmtime(fp)
            except:
                pass

    last_push = time.time()

    try:
        while True:
            changed = False
            for root, dirs, files in os.walk(WATCH_DIR):
                # Skip .git
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
                            last_modified[fp] = mtime
                    except:
                        pass

            if changed and time.time() - last_push > DEBOUNCE_SECONDS:
                print(f"\n[{datetime.now():%H:%M:%S}] Change detected! Deploying...")
                git_add_commit_push()
                last_push = time.time()

            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopped.")


def main():
    # First, do an immediate push to sync
    print("🔄 Syncing with GitHub...")
    git_add_commit_push()

    # Then watch
    watch()


if __name__ == "__main__":
    main()
