"""
Build Nexus Mobile APK from PWA using Android SDK tools.
Generates a signed WebView wrapper APK.
"""
import os, sys, subprocess, shutil, json
from pathlib import Path

SDK = Path(os.environ.get("ANDROID_HOME", os.environ.get("ANDROID_SDK_ROOT", "")))
if not SDK.exists():
    # Try common locations
    for p in [Path.home() / "AppData/Local/Android/Sdk",
              Path("C:/Android/Sdk"), Path("C:/android-sdk")]:
        if p.exists():
            SDK = p
            break

BUILD_DIR = Path(__file__).parent / "apk-build"
BUILD_TOOLS = sorted((SDK / "build-tools").glob("*"), reverse=True)
BUILD_TOOLS_VER = BUILD_TOOLS[0] if BUILD_TOOLS else None
PLATFORM = SDK / "platforms" / "android-36"
AAPT2 = BUILD_TOOLS_VER / "aapt2.exe" if BUILD_TOOLS_VER else None
D8 = BUILD_TOOLS_VER / "lib" / "d8.jar" if BUILD_TOOLS_VER else None
ZIPALIGN = BUILD_TOOLS_VER / "zipalign.exe" if BUILD_TOOLS_VER else None
APKSIGNER = BUILD_TOOLS_VER / "lib" / "apksigner.jar" if BUILD_TOOLS_VER else None
ANDROID_JAR = PLATFORM / "android.jar"
KEYSTORE = BUILD_DIR.parent / "android-build" / "android.keystore"

PACKAGE = "com.nexus.mobile"
PWA_URL = "https://gonzalitodev.github.io/h4ck3r-zone/nexus-mobile/"
APP_NAME = "Nexus Mobile"

print(f"SDK: {SDK}")
print(f"Build Tools: {BUILD_TOOLS_VER}")
print(f"Platform: {PLATFORM}")


def run(cmd, cwd=None):
    print(f"  RUN: {' '.join(str(c) for c in cmd)}")
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  STDERR: {r.stderr[:300]}")
    return r


def build():
    # Clean
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    # Step 1: Create Java source
    java_dir = BUILD_DIR / "java" / PACKAGE.replace(".", "/")
    java_dir.mkdir(parents=True)

    java_src = java_dir / "MainActivity.java"
    java_code = f'''
package {PACKAGE};
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.graphics.Color;

public class MainActivity extends Activity {{
    @Override
    protected void onCreate(Bundle saved) {{
        super.onCreate(saved);
        WebView wv = new WebView(this);
        wv.setBackgroundColor(Color.parseColor("#08080c"));
        WebSettings ws = wv.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setAllowFileAccess(false);
        ws.setCacheMode(WebSettings.LOAD_DEFAULT);
        wv.setWebViewClient(new WebViewClient());
        setContentView(wv);
        wv.loadUrl("{PWA_URL}");
    }}
}}
'''
    java_src.write_text(java_code)
    print("[1/6] Java source created")

    # Step 2: Compile Java to .class
    classes_dir = BUILD_DIR / "classes"
    classes_dir.mkdir()
    r = run(["javac",
             "-cp", str(ANDROID_JAR),
             "-d", str(classes_dir),
             str(java_src)])
    if not list(classes_dir.glob("**/*.class")):
        print("ERROR: Java compilation failed")
        return
    print("[2/6] Java compiled")

    # Step 3: Convert .class to .dex with d8
    dex_dir = BUILD_DIR / "dex"
    dex_dir.mkdir()
    classes_list = " ".join(str(p) for p in classes_dir.rglob("*.class"))
    r = run(["java", "-Xmx512M", "-cp", str(D8),
             "com.android.tools.r8.D8",
             "--lib", str(ANDROID_JAR),
             "--output", str(dex_dir),
             "--min-api", "24"] + [str(p) for p in classes_dir.rglob("*.class")])
    if not list(dex_dir.glob("*.dex")):
        print("ERROR: D8 conversion failed")
        return
    print("[3/6] DEX created")

    # Step 4: Create APK with aapt2
    manifest_dir = BUILD_DIR / "manifest"
    manifest_dir.mkdir()
    manifest_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{PACKAGE}" android:versionCode="1" android:versionName="1.0">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:label="{APP_NAME}" android:theme="@android:style/Theme.NoTitleBar"
        android:hardwareAccelerated="true" android:usesCleartextTraffic="true">
        <activity android:name=".MainActivity" android:exported="true"
            android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>'''
    (manifest_dir / "AndroidManifest.xml").write_text(manifest_xml)

    # Compile manifest
    compiled_dir = BUILD_DIR / "compiled"
    compiled_dir.mkdir()
    r = run([str(AAPT2), "compile", "--dir", str(manifest_dir), "-o", str(compiled_dir)])
    print("[4/6] Manifest compiled")

    # Link APK
    apk_unaligned = BUILD_DIR / "app-unaligned.apk"
    r = run([str(AAPT2), "link",
             "-o", str(apk_unaligned),
             "-I", str(ANDROID_JAR),
             "--manifest", str(manifest_dir / "AndroidManifest.xml"),
             "--min-sdk-version", "24",
             "--target-sdk-version", "36",
             "--version-code", "1",
             "--version-name", "1.0"] +
             [str(p) for p in compiled_dir.glob("*.flat")],
             cwd=str(BUILD_DIR))

    if not apk_unaligned.exists():
        print("ERROR: APK linking failed")
        return

    # Add dex to APK
    import zipfile
    with zipfile.ZipFile(apk_unaligned, 'a', zipfile.ZIP_DEFLATED) as z:
        for dex_file in dex_dir.glob("*.dex"):
            z.write(dex_file, dex_file.name)
    print("[5/6] APK assembled")

    # Step 5: Zipalign
    apk_aligned = BUILD_DIR / "app-aligned.apk"
    r = run([str(ZIPALIGN), "-f", "-p", "4",
             str(apk_unaligned), str(apk_aligned)])
    if not apk_aligned.exists():
        print("ERROR: Zipalign failed")
        return

    # Step 6: Sign
    apk_final = BUILD_DIR.parent / "NexusMobile.apk"
    r = run(["java", "-jar", str(APKSIGNER), "sign",
             "--ks", str(KEYSTORE),
             "--ks-pass", "pass:nexus123",
             "--ks-key-alias", "nexusmobile",
             "--key-pass", "pass:nexus123",
             "--out", str(apk_final),
             str(apk_aligned)])
    if not apk_final.exists():
        print("ERROR: Signing failed")
        return

    print(f"[6/6] APK SIGNED: {apk_final}")
    print(f"  Size: {apk_final.stat().st_size / 1024:.1f} KB")
    print(f"  Ready to install!")


if __name__ == "__main__":
    build()
