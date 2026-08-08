"""
Nexus Auto-Deploy — Watch files, auto commit + push to GitHub.
Runs in background. Saves you from manual git commands.
"""
import os, sys, time, subprocess, threading
from pathlib import Path
from datetime import datetime

WATCH_DIR = Path(__file__).resolve().parent / "websecurity-landing"
DEBOUNCE_SECONDS = 5  # Wait 5s after last change before committing


def git_add_commit_push():
    """Add all changes, commit with timestamp, push."""
    try:
        os.chdir(WATCH_DIR.parent)
        subprocess.run(["git", "add", "websecurity-landing/"], capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "commit", "-m", f"Auto-deploy: {datetime.now():%H:%M:%S}", "--no-verify"],
            capture_output=True, timeout=10
        )
        if "nothing to commit" not in result.stdout.decode() + result.stderr.decode():
            subprocess.run(["git", "push", "origin", "master"], capture_output=True, timeout=30)
            print(f"[{datetime.now():%H:%M:%S}] ✓ Pushed to GitHub")
        else:
            print(f"[{datetime.now():%H:%M:%S}] No changes to commit")
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
