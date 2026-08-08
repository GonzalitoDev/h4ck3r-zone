"""Build Nexus GPS APK"""
import os, sys, subprocess, shutil, zipfile
from pathlib import Path

SDK = Path(os.environ.get("ANDROID_HOME",
      os.environ.get("ANDROID_SDK_ROOT",
      str(Path.home() / "AppData/Local/Android/Sdk"))))
BT = sorted((SDK / "build-tools").glob("*"), reverse=True)[0]
PLATFORM = SDK / "platforms" / "android-36"
AAPT2 = BT / "aapt2.exe"; D8_JAR = BT / "lib" / "d8.jar"
ANDROID_JAR = PLATFORM / "android.jar"
KEYSTORE = Path.home() / "Desktop/Programacion v2/Nexus Bot/nexus-mobile/android-build/android.keystore"
PACKAGE = "com.nexus.gps"; BUILD_DIR = Path(__file__).parent / "apk-build"
HTML_SRC = Path(__file__).parent / "index.html"

def run(cmd, cwd=None):
    print(f"  {' '.join(str(c) for c in cmd)[:100]}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
BUILD_DIR.mkdir(parents=True)

# Assets
(BUILD_DIR / "assets").mkdir()
shutil.copy(HTML_SRC, BUILD_DIR / "assets" / "index.html")
print("[1/7] HTML")

# Java
java_dir = BUILD_DIR / "java" / PACKAGE.replace(".", "/"); java_dir.mkdir(parents=True)
(java_dir / "MainActivity.java").write_text(f'''package {PACKAGE};
import android.app.Activity; import android.os.Bundle;
import android.webkit.*; import android.graphics.Color;
public class MainActivity extends Activity{{
  @Override protected void onCreate(Bundle s){{
    super.onCreate(s);
    WebView w=new WebView(this);
    w.setBackgroundColor(Color.parseColor("#0a0a0f"));
    WebSettings ws=w.getSettings();
    ws.setJavaScriptEnabled(true); ws.setDomStorageEnabled(true);
    ws.setGeolocationEnabled(true); ws.setAllowFileAccess(true);
    w.setWebViewClient(new WebViewClient());
    setContentView(w);
    w.loadUrl("file:///android_asset/index.html");
  }}
}}''')
print("[2/7] Java")

# Compile
classes_dir = BUILD_DIR / "classes"; classes_dir.mkdir()
run(["javac","-cp",str(ANDROID_JAR),"-d",str(classes_dir),str(java_dir/"MainActivity.java")])
print("[3/7] Compiled")

# DEX
dex_dir = BUILD_DIR / "dex"; dex_dir.mkdir()
run(["java","-Xmx512M","-cp",str(D8_JAR),"com.android.tools.r8.D8",
     "--lib",str(ANDROID_JAR),"--output",str(dex_dir),"--min-api","24"]
     + [str(p) for p in classes_dir.rglob("*.class")])
print("[4/7] DEX")

# Manifest
manifest_dir = BUILD_DIR / "manifest"; manifest_dir.mkdir()
(manifest_dir / "AndroidManifest.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{PACKAGE}" android:versionCode="1" android:versionName="1.0">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <application android:label="Nexus GPS" android:theme="@android:style/Theme.NoTitleBar"
        android:hardwareAccelerated="true" android:usesCleartextTraffic="true"
        android:icon="@android:drawable/ic_menu_compass">
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
run([str(AAPT2),"compile","--dir",str(manifest_dir),"-o",str(compiled_dir)])
print("[5/7] Resources")

# Link
apk = BUILD_DIR / "app-unaligned.apk"
run([str(AAPT2),"link","-o",str(apk),"-I",str(ANDROID_JAR),
     "--manifest",str(manifest_dir/"AndroidManifest.xml"),
     "--min-sdk-version","24","--target-sdk-version","36",
     "--version-code","1","--version-name","1.0",
     "-A",str(BUILD_DIR/"assets")] + [str(p) for p in compiled_dir.glob("*.flat")])

with zipfile.ZipFile(apk, 'a', zipfile.ZIP_DEFLATED) as z:
    for df in dex_dir.glob("*.dex"): z.write(df, df.name)
print("[6/7] APK")

# Sign
aligned = BUILD_DIR / "app-aligned.apk"
run([str(BT/"zipalign.exe"),"-f","-p","4",str(apk),str(aligned)])
final = Path(__file__).parent / "NexusGPS.apk"
run(["java","-jar",str(BT/"lib/apksigner.jar"),"sign","--ks",str(KEYSTORE),
     "--ks-pass","pass:nexus123","--ks-key-alias","nexusmobile",
     "--key-pass","pass:nexus123","--out",str(final),str(aligned)])
print(f"[7/7] DONE: {final} ({final.stat().st_size/1024:.0f} KB)")
