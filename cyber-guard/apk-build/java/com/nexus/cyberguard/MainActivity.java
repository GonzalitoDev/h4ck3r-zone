package com.nexus.cyberguard;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.graphics.Color;
public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle s) {
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
    }
}