const PWA_CACHE_NAME = "loading-arena-pwa-v1";

const PWA_CACHE_URLS = [
  "/pwa",
  "/pwa/feed",
  "/pwa/record",
  "/pwa/leaderboard",
  "/pwa/profile",
  "/pwa/manifest.json",
  "/pwa/static/css/pwa.css",
  "/pwa/static/js/pwa.js",
  "/pwa/static/icons/pwa-icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(PWA_CACHE_NAME).then((cache) => cache.addAll(PWA_CACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== PWA_CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const requestUrl = new URL(event.request.url);

  if (requestUrl.origin !== self.location.origin || !requestUrl.pathname.startsWith("/pwa")) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        if (event.request.method === "GET") {
          const responseClone = networkResponse.clone();
          caches.open(PWA_CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        }
        return networkResponse;
      });
    })
  );
});
