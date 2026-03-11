const CACHE = 'fars-jukebox-v20';
const PRECACHE = [
  '/', '/manifest.json',
  // MP3 filer
  '/audio/sandheden-bag-muren.mp3',
  '/audio/bare-en-far.mp3', '/audio/kristoffer.mp3', '/audio/som-en-kokosnoed.mp3',
  '/audio/mine-drenge.mp3', '/audio/en-fars-kamp.mp3',
  '/audio/brormand.mp3', '/audio/hvad-boern-ved.mp3', '/audio/hjem.mp3', '/audio/lad-dem-snakke.mp3',
  '/audio/i-nat.mp3', '/audio/godnat-skam.mp3',
  '/audio/rubble-robo-venner.mp3', '/audio/lige-om-lidt.mp3',
  '/audio/hoejere.mp3', '/audio/min-tur.mp3', '/audio/giv-os-mere.mp3',
  // Videoer
  '/audio/sandheden-bag-muren-video-v22.mp4',
  '/audio/bare-en-far-video.mp4', '/audio/kristoffer-video.mp4',
  '/audio/lad-dem-snakke-video.mp4', '/audio/i-nat-video.mp4',
  '/audio/hoejere-video.mp4', '/audio/giv-os-mere-video.mp4',
  // Cover art
  '/audio/sandheden-bag-muren-art.png',
  '/audio/bare-en-far-art.svg', '/audio/kristoffer-art.svg', '/audio/kokosnoed-art.svg',
  '/audio/mine-drenge-art.svg', '/audio/fars-kamp-art.svg',
  '/audio/brormand-art.jpg', '/audio/hvad-boern-ved-art.png', '/audio/hjem-art.png', '/audio/lad-dem-snakke-art.png',
  '/audio/i-nat-art.svg', '/audio/godnat-skam-art.svg',
  '/audio/rubble-art.svg', '/audio/lige-om-lidt-art.svg',
  '/audio/hoejere-art.svg', '/audio/hoejere-art.png', '/audio/min-tur-art.svg', '/audio/min-tur-art.png', '/audio/giv-os-mere-art.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Never cache admin or API paths
  if (url.pathname.startsWith('/admin') || url.pathname.startsWith('/api/')) return;
  // Skip tracking endpoints
  if (url.pathname === '/np' || url.pathname === '/track') return;
  if (url.pathname.endsWith('.mp3') || url.pathname.endsWith('.mp4')) {
    e.respondWith(handleAudio(e.request));
  } else if (e.request.mode === 'navigate' || url.pathname === '/') {
    // Network-first for HTML pages
    e.respondWith(fetch(e.request).then(r => {
      caches.open(CACHE).then(c => { c.put(e.request, r.clone()); }).catch(() => {});
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
      const parsed = parseByteRange(range, total);
      if (!parsed) {
        return new Response(null, { status: 416, headers: { 'Content-Range': `bytes */${total}` } });
      }
      const { start, end } = parsed;
      return new Response(blob.slice(start, end + 1), {
        status: 206,
        headers: {
          'Content-Range': `bytes ${start}-${end}/${total}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': end - start + 1,
          'Content-Type': req.url.endsWith('.mp4') ? 'video/mp4' : 'audio/mpeg'
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

function parseByteRange(rangeHeader, total) {
  const match = /^bytes=(\d*)-(\d*)$/i.exec((rangeHeader || '').trim());
  if (!match) return null;

  let start;
  let end;

  if (!match[1] && match[2]) {
    const suffix = parseInt(match[2], 10);
    if (!Number.isFinite(suffix) || suffix <= 0) return null;
    start = Math.max(0, total - suffix);
    end = total - 1;
  } else {
    start = match[1] ? parseInt(match[1], 10) : 0;
    end = match[2] ? parseInt(match[2], 10) : total - 1;
  }

  if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
  if (start < 0 || start > end || end >= total) return null;
  return { start, end };
}
