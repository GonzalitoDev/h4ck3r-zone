const CACHE = "nexus-breach-v1";
const FILES = ["index.html", "manifest.json", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(clients.claim());
});
self.addEventListener("fetch", e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).catch(() => new Response("Offline - Secure channel lost", { status: 503 }))));
});
