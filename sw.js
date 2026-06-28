const COSMO_CACHE = 'cosmo-kid-v41';
const CORE = [
  './',
  './index.html?v=41',
  './game.html?v=41',
  './game3d.html?v=41',

  './diagnostico.html?v=41',
  './manifest.webmanifest',
  './assets/icons/icon-192.png',
  './assets/icons/icon-512.png'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open(COSMO_CACHE).then(cache => cache.addAll(CORE).catch(()=>{})));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== COSMO_CACHE).map(k => caches.delete(k)))).then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);
  if(req.method !== 'GET') return;

  // HTML: network first para evitar versiones viejas.
  if(req.headers.get('accept')?.includes('text/html') || url.pathname.endsWith('.html') || url.pathname.endsWith('/')) {
    event.respondWith(
      fetch(req, {cache:'no-store'}).then(res => {
        const copy = res.clone();
        caches.open(COSMO_CACHE).then(cache => cache.put(req, copy));
        return res;
      }).catch(() => caches.match(req).then(cached => cached || caches.match('./index.html?v=41')))
    );
    return;
  }

  // Assets: cache first.
  event.respondWith(
    caches.match(req).then(cached => cached || fetch(req).then(res => {
      const copy = res.clone();
      caches.open(COSMO_CACHE).then(cache => cache.put(req, copy));
      return res;
    }).catch(()=>cached))
  );
});
