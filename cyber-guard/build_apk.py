"""
Build CyberGuard APK - fully offline security app.
Loads HTML from local assets (no internet required).
"""
import os, sys, subprocess, shutil, zipfile
from pathlib import Path

SDK = Path(os.environ.get("ANDROID_HOME",
          os.environ.get("ANDROID_SDK_ROOT",
          str(Path.home() / "AppData/Local/Android/Sdk"))))
BUILD_TOOLS = sorted((SDK / "build-tools").glob("*"), reverse=True)
BT = BUILD_TOOLS[0]
PLATFORM = SDK / "platforms" / "android-36"
AAPT2 = BT / "aapt2.exe"
D8_JAR = BT / "lib" / "d8.jar"
ANDROID_JAR = PLATFORM / "android.jar"
ZIPALIGN = BT / "zipalign.exe"
APKSIGNER = BT / "lib" / "apksigner.jar"
KEYSTORE = Path.home() / "Desktop/Programacion v2/Nexus Bot/nexus-mobile/android-build/android.keystore"

PACKAGE = "com.nexus.cyberguard"
BUILD_DIR = Path(__file__).parent / "apk-build"
HTML_SRC = Path(__file__).parent / "index.html"

def run(cmd, cwd=None):
    print(f"  {' '.join(str(c) for c in cmd)[:120]}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

# Clean
if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
BUILD_DIR.mkdir(parents=True)

# Step 1: Assets directory with HTML
assets_dir = BUILD_DIR / "assets"
assets_dir.mkdir()
shutil.copy(HTML_SRC, assets_dir / "index.html")
print("[1/7] HTML copied to assets")

# Step 2: Java source (loads local HTML)
java_dir = BUILD_DIR / "java" / PACKAGE.replace(".", "/")
java_dir.mkdir(parents=True)
java_src = java_dir / "MainActivity.java"
java_code = f'''package {PACKAGE};
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.graphics.Color;
public class MainActivity extends Activity {{
    @Override protected void onCreate(Bundle s) {{
        super.onCreate(s);
        WebView w = new WebView(this);
        w.setBackgroundColor(Color.parseColor("#06080d"));
        WebSettings ws = w.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setAllowFileAccess(true);
        w.setWebViewClient(new WebViewClient());
        setContentView(w);
        w.loadUrl("file:///android_asset/index.html");
    }}
}}'''
java_src.write_text(java_code)
print("[2/7] Java source")

# Step 3: Compile
classes_dir = BUILD_DIR / "classes"; classes_dir.mkdir()
r = run(["javac","-cp",str(ANDROID_JAR),"-d",str(classes_dir),str(java_src)])
print("[3/7] Compiled")

# Step 4: DEX
dex_dir = BUILD_DIR / "dex"; dex_dir.mkdir()
r = run(["java","-Xmx512M","-cp",str(D8_JAR),"com.android.tools.r8.D8",
         "--lib",str(ANDROID_JAR),"--output",str(dex_dir),"--min-api","24"]
         + [str(p) for p in classes_dir.rglob("*.class")])
print("[4/7] DEX")

# Step 5: Manifest + Resources
manifest_dir = BUILD_DIR / "manifest"; manifest_dir.mkdir()
(manifest_dir / "AndroidManifest.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{PACKAGE}" android:versionCode="1" android:versionName="1.0">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:label="CyberGuard" android:theme="@android:style/Theme.NoTitleBar"
        android:hardwareAccelerated="true" android:usesCleartextTraffic="true"
        android:icon="@android:drawable/ic_lock_idle_lock">
        <activity android:name=".MainActivity" android:exported="true"
            android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>''')

compiled_dir = BUILD_DIR / "compiled"; compiled_dir.mkdir()
r = run([str(AAPT2),"compile","--dir",str(manifest_dir),"-o",str(compiled_dir)])
print("[5/7] Resources")

# Step 6: Link APK
apk_path = BUILD_DIR / "app-unaligned.apk"
r = run([str(AAPT2),"link","-o",str(apk_path),"-I",str(ANDROID_JAR),
         "--manifest",str(manifest_dir/"AndroidManifest.xml"),
         "--min-sdk-version","24","--target-sdk-version","36",
         "--version-code","1","--version-name","1.0",
         "-A",str(assets_dir)] +
         [str(p) for p in compiled_dir.glob("*.flat")], cwd=str(BUILD_DIR))

# Add DEX to APK
with zipfile.ZipFile(apk_path, 'a', zipfile.ZIP_DEFLATED) as z:
    for df in dex_dir.glob("*.dex"): z.write(df, df.name)
print("[6/7] APK assembled")

# Step 7: Align + Sign
aligned = BUILD_DIR / "app-aligned.apk"
r = run([str(ZIPALIGN),"-f","-p","4",str(apk_path),str(aligned)])

final_apk = Path(__file__).parent / "CyberGuard.apk"
r = run(["java","-jar",str(APKSIGNER),"sign","--ks",str(KEYSTORE),
         "--ks-pass","pass:nexus123","--ks-key-alias","nexusmobile",
         "--key-pass","pass:nexus123","--out",str(final_apk),str(aligned)])

print(f"[7/7] DONE: {final_apk} ({final_apk.stat().st_size/1024:.0f} KB)")
