const C = "nexus-mobile-v1";
const F = ["index.html", "manifest.json", "icons/icon-192.png", "icons/icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(F))) });
self.addEventListener("activate", e => { e.waitUntil(caches.delete(C + "-old").then(() => clients.claim())) });
self.addEventListener("fetch", e => { e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))) });
