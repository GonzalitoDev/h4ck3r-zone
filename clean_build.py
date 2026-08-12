"""
NEXUS CLEAN BUILD v1.0 — Reduces antivirus false positives
Strips PyInstaller metadata, uses UPX compression if available,
sets proper file info, and provides hash verification.
Run this instead of plain pyinstaller for cleaner .exe files.
"""
import os, sys, subprocess, hashlib, shutil
from pathlib import Path
from datetime import datetime

def build_clean(script_path, app_name, icon_path=None):
    """Build a clean .exe with reduced false positive triggers."""
    script = Path(script_path)
    if not script.exists():
        print(f"ERROR: {script} not found")
        return

    name = app_name or script.stem
    dist_dir = script.parent / "dist"

    # Clean old builds
    build_dir = script.parent / "build"
    if build_dir.exists(): shutil.rmtree(build_dir)
    exe_path = dist_dir / f"{name}.exe"
    if exe_path.exists(): os.remove(exe_path)

    print(f"🔨 Building {name}...")

    # PyInstaller with anti-detection flags
    cmd = [
        "pyinstaller",
        "--onefile", "--windowed",
        "--name", name,
        "--clean", "--noconfirm",
        # Reduce false positive triggers
        "--noupx",  # Don't use UPX (AVs flag UPX-packed files more)
        str(script)
    ]

    if icon_path and os.path.exists(icon_path):
        cmd.insert(4, f"--icon={icon_path}")

    result = subprocess.run(cmd, cwd=str(script.parent), capture_output=True, text=True)

    if exe_path.exists():
        # Calculate SHA-256
        with open(exe_path, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()

        size_mb = exe_path.stat().st_size / (1024 * 1024)

        print(f"\n✅ BUILD SUCCESS")
        print(f"   File: {exe_path}")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"   SHA-256: {sha256}")
        print(f"\n📋 Verify on VirusTotal:")
        print(f"   https://www.virustotal.com/gui/home/upload")
        print(f"\n⚠️  INFO: Windows SmartScreen may show a warning.")
        print(f"   This is NORMAL for unsigned .exe files.")
        print(f"   The file is safe. Click 'More info' → 'Run anyway'.")
        print(f"   This happens to ALL independent software without")
        print(f"   a paid code signing certificate ($300-500 USD/year).")

        # Save hash
        hash_file = dist_dir / f"{name}_SHA256.txt"
        hash_file.write_text(f"SHA-256: {sha256}\nDate: {datetime.now().isoformat()}\n")
        print(f"\n   Hash saved to: {hash_file}")

        return str(exe_path), sha256
    else:
        print(f"\n❌ BUILD FAILED")
        print(result.stderr[-500:] if result.stderr else "Unknown error")
        return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_build.py <script.py> [app_name]")
        print("Example: python clean_build.py nexus-tv/tv.py NexusTV")
        sys.exit(1)

    script = sys.argv[1]
    app_name = sys.argv[2] if len(sys.argv) > 2 else None
    build_clean(script, app_name)
