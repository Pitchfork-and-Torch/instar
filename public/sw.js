/* INSTAR service worker. Offline school. Kill switch at top. */
const KILL = false;
const CACHE = "instar-1.1.6";
const PRECACHE = [
  "/",
  "/workbench/",
  "/manual/",
  "/husk/",
  "/brood/",
  "/nymph/",
  "/soil/",
  "/tunnel/",
  "/song/",
  "/prime/",
  "/liber/",
  "/emerge/",
  "/css/instar.css",
  "/js/core.js",
  "/js/puzzle.js",
  "/js/ciphers.js",
  "/js/stego.js",
  "/js/spec.js",
  "/js/rsa.js",
  "/js/runes.js",
  "/js/workbench.js",
  "/js/page56.js",
  "/fonts/fontshare/fonts.css",
  "/fonts/fontshare/tokens.css",
  "/media/seal.jpg",
  "/media/grain.png",
  "/media/hero-soil.jpg",
  "/media/wing.png",
  "/media/emergence.wav",
  "/library/soil-journal.txt",
  "/static/clutch.txt",
  "/manifest.webmanifest",
];

self.addEventListener("install", function (event) {
  if (KILL) {
    self.skipWaiting();
    return;
  }
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(PRECACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (k) {
            return k !== CACHE;
          })
          .map(function (k) {
            return caches.delete(k);
          })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  if (KILL) {
    event.waitUntil(
      caches.keys().then(function (keys) {
        return Promise.all(keys.map(function (k) { return caches.delete(k); }));
      }).then(function () {
        return self.registration.unregister();
      })
    );
    return;
  }
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  const accept = event.request.headers.get("accept") || "";
  const isDoc = event.request.mode === "navigate" || accept.indexOf("text/html") !== -1;

  if (isDoc) {
    event.respondWith(networkFirst(event.request));
  } else {
    event.respondWith(cacheFirst(event.request));
  }
});

function networkFirst(request) {
  return fetch(request)
    .then(function (res) {
      const copy = res.clone();
      caches.open(CACHE).then(function (cache) {
        cache.put(request, copy);
      });
      return res;
    })
    .catch(function () {
      return caches.match(request).then(function (hit) {
        return hit || caches.match("/");
      });
    });
}

function cacheFirst(request) {
  return caches.match(request).then(function (hit) {
    if (hit) return hit;
    return fetch(request).then(function (res) {
      const copy = res.clone();
      caches.open(CACHE).then(function (cache) {
        cache.put(request, copy);
      });
      return res;
    });
  });
}
