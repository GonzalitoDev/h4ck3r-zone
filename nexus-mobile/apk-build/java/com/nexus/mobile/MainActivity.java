
package com.nexus.mobile;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.graphics.Color;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle saved) {
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
        wv.loadUrl("https://gonzalitodev.github.io/h4ck3r-zone/nexus-mobile/");
    }
}
