package com.nexus.gps;
import android.app.Activity; import android.os.Bundle;
import android.webkit.*; import android.graphics.Color;
public class MainActivity extends Activity{
  @Override protected void onCreate(Bundle s){
    super.onCreate(s);
    WebView w=new WebView(this);
    w.setBackgroundColor(Color.parseColor("#0a0a0f"));
    WebSettings ws=w.getSettings();
    ws.setJavaScriptEnabled(true); ws.setDomStorageEnabled(true);
    ws.setGeolocationEnabled(true); ws.setAllowFileAccess(true);
    w.setWebViewClient(new WebViewClient());
    setContentView(w);
    w.loadUrl("file:///android_asset/index.html");
  }
}