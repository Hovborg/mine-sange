export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Kun /audio/ paths
    if (!url.pathname.startsWith('/audio/')) {
      return fetch(request);
    }

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': 'https://sang.hovborg.tech',
          'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
          'Access-Control-Allow-Headers': 'Range',
          'Access-Control-Max-Age': '86400',
        }
      });
    }

    // Hotlink-beskyttelse
    const referer = request.headers.get('Referer') || '';
    if (referer && !referer.includes('sang.hovborg.tech') && !referer.includes('localhost')) {
      return new Response('Forbidden', { status: 403 });
    }

    const key = url.pathname.slice(1); // fjern leading /
    const range = request.headers.get('Range');

    // Hent fra R2 med range support
    const options = {};
    if (range) {
      const match = range.match(/bytes=(\d*)-(\d*)/);
      if (match) {
        options.range = {};
        if (match[1]) options.range.offset = parseInt(match[1]);
        if (match[2]) options.range.length = match[2] ? parseInt(match[2]) - (parseInt(match[1]) || 0) + 1 : undefined;
      }
    }

    const object = await env.MEDIA.get(key, options);
    if (!object) {
      return new Response('Not Found', { status: 404 });
    }

    // Content-Type baseret på filendelse
    const ext = key.split('.').pop().toLowerCase();
    const contentTypes = {
      mp3: 'audio/mpeg',
      mp4: 'video/mp4',
      svg: 'image/svg+xml',
      png: 'image/png',
      jpg: 'image/jpeg',
      jpeg: 'image/jpeg',
    };

    const headers = new Headers();
    headers.set('Content-Type', contentTypes[ext] || 'application/octet-stream');
    headers.set('Accept-Ranges', 'bytes');
    headers.set('Access-Control-Allow-Origin', 'https://sang.hovborg.tech');
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');

    // Range response
    if (range && object.range) {
      const start = object.range.offset || 0;
      const end = start + object.range.length - 1;
      headers.set('Content-Range', `bytes ${start}-${end}/${object.size}`);
      headers.set('Content-Length', object.range.length);
      return new Response(object.body, { status: 206, headers });
    }

    headers.set('Content-Length', object.size);
    return new Response(object.body, { status: 200, headers });
  }
};
