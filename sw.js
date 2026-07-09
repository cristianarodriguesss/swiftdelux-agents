const CACHE_NAME = "the-agency-v1";
const URLS_TO_CACHE = [
  "/swiftdelux-agents/",
  "/swiftdelux-agents/index.html",
  "/swiftdelux-agents/dados.json"
];

self.addEventListener("install", function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) { return key !== CACHE_NAME; })
            .map(function(key) { return caches.delete(key); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function(event) {
  // Always fetch dados.json fresh from network
  if (event.request.url.includes("dados.json")) {
    event.respondWith(
      fetch(event.request).catch(function() {
        return caches.match(event.request);
      })
    );
    return;
  }
  // For everything else, cache first
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request).then(function(fetchResponse) {
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, fetchResponse.clone());
        });
        return fetchResponse;
      });
    })
  );
});