const CACHE = 'fars-jukebox-v2';
const PRECACHE = [
  '/', '/manifest.json',
  '/audio/bare-en-far.mp3', '/audio/kristoffer.mp3', '/audio/som-en-kokosnoed.mp3',
  '/audio/mine-drenge.mp3', '/audio/en-fars-kamp.mp3', '/audio/stop-saa-brian.mp3',
  '/audio/brormand.mp3', '/audio/hvad-boern-ved.mp3', '/audio/hjem.mp3', '/audio/lad-dem-snakke.mp3',
  '/audio/bare-en-far-art.png', '/audio/kristoffer-art.png', '/audio/kokosnoed-art.png',
  '/audio/mine-drenge-art.png', '/audio/fars-kamp-art.png', '/audio/stop-brian-art.svg',
  '/audio/brormand-art.jpg', '/audio/hvad-boern-ved-art.png', '/audio/hjem-art.png', '/audio/lad-dem-snakke-art.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Never cache admin paths
  if (url.pathname.startsWith('/admin')) return;
  if (url.pathname.endsWith('.mp3')) {
    e.respondWith(handleAudio(e.request));
  } else if (e.request.mode === 'navigate' || url.pathname === '/') {
    // Network-first for HTML pages
    e.respondWith(fetch(e.request).then(r => {
      const cache = caches.open(CACHE).then(c => { c.put(e.request, r.clone()); });
      return r;
    }).catch(() => caches.match(e.request)));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});

async function handleAudio(req) {
  const cache = await caches.open(CACHE);
  const range = req.headers.get('range');

  // Try cache first for range requests
  if (range) {
    const cached = await cache.match(req.url, { ignoreSearch: true, ignoreVary: true });
    if (cached) {
      const blob = await cached.blob();
      const total = blob.size;
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : total - 1;
      if (isNaN(start) || isNaN(end) || start < 0 || end >= total || start > end) {
        return new Response(null, { status: 416, headers: { 'Content-Range': `bytes */${total}` } });
      }
      return new Response(blob.slice(start, end + 1), {
        status: 206,
        headers: {
          'Content-Range': `bytes ${start}-${end}/${total}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': end - start + 1,
          'Content-Type': 'audio/mpeg'
        }
      });
    }
  }

  // Non-range or not cached: try network, fallback to cache
  try {
    const res = await fetch(req);
    if (res.ok && !range) {
      cache.put(req.url, res.clone());
    }
    return res;
  } catch {
    const cached = await cache.match(req.url, { ignoreSearch: true, ignoreVary: true });
    return cached || new Response('Offline', { status: 503 });
  }
}
