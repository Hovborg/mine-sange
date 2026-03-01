# Fars Jukebox - Musik Deling Platform

## Scope
Musik deling platform/app hostet på `sang.hovborg.tech`.
Arbejd KUN med musik deling kode.

## Regler
- Fokus: Musik deling funktionalitet
- Ignorer alt der ikke er musik deling relateret
- Skriv alt UI-tekst på dansk
- Behold den eksisterende Spotify-lignende dark theme æstetik

## Arkitektur
- **Ingen build-process** — ren HTML/CSS/JS, ingen frameworks
- **Single-file HTML apps** — al CSS og JS er inline i HTML-filerne
- Hostet via **GitHub Pages** med custom domain (CNAME: `sang.hovborg.tech`)
- **PWA** med service worker (`sw.js`) og manifest (`manifest.json`)

## Sider
| Fil | Formål |
|-----|--------|
| `index.html` | Hovedside — sangliste + fuldt musikafspiller med karaoke lyrics |
| `hitboxen.html` | Hit-Boxen — separat sangside med egne sange |
| `kristoffer.html` | Dedikeret side til Kristoffer |
| `admin.html` | Admin-panel (statistik, login påkrævet) |
| `sang-stats.py` | Python script der parser nginx logs → stats.json |
| `sw.js` | Service Worker (cache v4) |

## Admin credentials
- Brugernavn: `admin`
- Password: `Mikkel2111nov`
- Auth: SHA-256 client-side, sessionStorage

## Nøgle-patterns
- Sange defineres som JS-array `songs[]` med id, title, file, image, gradient, glow, duration, lyrics
- Lyrics bruger word-by-word timing: `{t: timestamp, text: "linje", w: [per-word-timestamps]}`
- `stable-ts` forced alignment bruges til at generere præcise ord-timestamps
- Audio filer i `/audio/` — MP3 format
- Cover art i `/audio/` — SVG eller PNG format
- Service Worker cacher alle sange og art for offline brug
- MediaSession API til lock screen controls
- Chromecast + AirPlay integration
- WebGL shader background reagerer på audio-analyse
- Vibrant.js til dynamisk farve-extraktion fra album art
- Keyboard shortcuts: Space, Arrow, N, P, R, L, M, Escape

## Konventioner
- Variabler og funktioner: camelCase
- CSS: BEM-lignende med kebab-case klasser
- Farver: CSS custom properties (`--bg`, `--text`, `--accent` osv.)
- Animationer: CSS transitions + JS requestAnimationFrame loops
- Alle sange har `duration` i sekunder og `lyrics[]` med timestamps

## Vigtigt
- Rør IKKE lyrics timestamps medmindre specifikt bedt om det
- Behold Google Cast og AirPlay integration
- Test altid at service worker cache-listen matcher faktiske filer
- `og-image.png` bruges til social sharing
