# Fars Jukebox - Musik Deling Platform

## Scope
Musik deling platform/app hostet på `sang.hovborg.tech`.
Arbejd KUN med musik deling kode.

## Regler
- Fokus: Musik deling funktionalitet
- Ignorer alt der ikke er musik deling relateret
- Skriv alt UI-tekst på dansk
- Behold den eksisterende Spotify-lignende dark theme æstetik

## Hosting & Infrastruktur

### Arkitektur
```
GitHub repo (Hovborg/mine-sange) → push til main → GitHub Pages → Cloudflare CDN → sang.hovborg.tech
```

- **GitHub Pages** — hosting, deployer automatisk ved push til `main`
- **Cloudflare** — CDN/proxy foran GitHub Pages, cacher alt (edge i København)
- **CNAME** — `sang.hovborg.tech` peger på GitHub Pages via Cloudflare DNS
- **Ingen lokal server nødvendig** — siden kører 100% i skyen
- **Ved PC-genstart:** Intet skal genstartes. Siden er altid online
- **Uptime:** GitHub Pages 99.99% + Cloudflare failover = siden går ikke ned

### Sådan opdateres siden
1. Rediger filer lokalt i `C:\codex_projekts\services\musik-deling\` (WSL: `/mnt/c/codex_projekts/services/musik-deling/`)
2. `git add <filer>` + `git commit` + `git push origin main`
3. GitHub Pages deployer automatisk inden for 1-2 minutter
4. Cloudflare cacher opdateringen på edge
5. Service Worker i browsere opdaterer sig selv ved næste besøg

### Git credentials fra WSL
- Remote: `https://github.com/Hovborg/mine-sange.git`
- Credential helper: Windows Git Credential Manager via `"/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"`
- Hvis push fejler: Kør `git config credential.helper store` og hent credentials fra Windows credential manager
- `core.fileMode` skal være `false` i WSL (undgår chmod-ændringer)

## Teknisk Arkitektur
- **Ingen build-process** — ren HTML/CSS/JS, ingen frameworks
- **Single-file HTML apps** — al CSS og JS er inline i HTML-filerne
- **PWA** med service worker (`sw.js`) og manifest (`manifest.json`)

## Filstruktur
```
musik-deling/
├── index.html          # Hovedside — 11 sange med karaoke lyrics
├── hitboxen.html       # Hit-Boxen — 4 sange (Giv Os Mere, Lige Om Lidt, Højere, Min Tur)
├── kristoffer.html     # Mix — 2 sange (Rubble og Robo-Venner, Brormand)
├── admin.html          # Admin-panel (statistik, login påkrævet)
├── sw.js               # Service Worker (cache version bumpes ved ændringer)
├── manifest.json       # PWA manifest
├── og-image.png        # OG-billede til social sharing (1200x630 PNG)
├── CNAME               # GitHub Pages custom domain
├── .nojekyll           # Tillader binære filer (MP3/MP4) på GitHub Pages
├── CHANGELOG.md        # Projekt-changelog
├── sang-stats.py       # Parser nginx logs → stats.json (kører på server)
└── audio/              # Alle mediefiler
    ├── *.mp3           # Sangfiler
    ├── *-art.svg/png   # Cover art
    └── *-video.mp4     # Musikvideoer
```

## Sider og Sange

### index.html — Hovedsiden (11 sange)
1. Sandheden Bag Muren
2. En Fars Kamp for Sine Børn
3. KRISTOFFER!
4. Som en Kokosnød
5. Mine Drenge
6. Bare En Far
7. Hvad Børn Ved
8. Hjem
9. Lad Dem Snakke
10. I Nat
11. Godnat, Skam

### hitboxen.html — Hit-Boxen (4 sange)
1. Giv Os Mere
2. Lige Om Lidt
3. Højere
4. Min Tur

### kristoffer.html — Mix (2 sange)
1. Rubble og Robo-Venner
2. Brormand

### Fjernede sange (filer bevaret i audio/, men ikke vist)
- Stop Så Brian — fjernet pga. juridisk risiko (offentliggør private beskeder)

## Admin Credentials
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
- Vibrant.js til dynamisk farve-extraktion fra album art
- Keyboard shortcuts: Space, Arrow, N, P, R, L, M, Escape

## Konventioner
- Variabler og funktioner: camelCase
- CSS: BEM-lignende med kebab-case klasser
- Farver: CSS custom properties (`--bg`, `--text`, `--accent` osv.)
- Animationer: CSS transitions + JS requestAnimationFrame loops
- Alle sange har `duration` i sekunder og `lyrics[]` med timestamps

## Tilføj ny sang — hvad skal du bruge?

1. **MP3-fil** — Placeres i `/audio/` (f.eks. `audio/sang-navn.mp3`)
2. **Cover art** — SVG eller PNG i `/audio/` (f.eks. `audio/sang-navn-art.svg`)
3. **Sangtitel**, **Sang-id** (kebab-case), **Varighed** (sekunder)
4. **Gradient-farver** (3 farver) og **Glow-farve**
5. **Lyrics med timestamps** — genereres med `stable-ts` forced alignment

### Filer der skal opdateres:
- **HTML-fil** (index.html/hitboxen.html/kristoffer.html) — Tilføj sang-objekt til `songs[]`
- **sw.js** — Tilføj MP3 og art til `PRECACHE[]`, bump cache version (`fars-jukebox-vN`)
- **sang-stats.py** — Tilføj sang-id til `VALID_SONGS` set
- **admin.html** — Tilføj sang til `SONG_COLORS` og `SONG_NAMES`

## OG / Social Sharing
- `og-image.png` i roden (IKKE i `/audio/`) — 1200x630 PNG
- OG tags i `<head>` af index.html peger på `https://sang.hovborg.tech/og-image.png`
- Facebook cache kan tvinges opdateret via [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)

## Vigtigt
- Rør IKKE lyrics timestamps medmindre specifikt bedt om det
- Behold Google Cast og AirPlay integration
- Test altid at service worker cache-listen matcher faktiske filer
- Bump ALTID `sw.js` cache version ved ændringer (`fars-jukebox-vN`)
- Opdater altid `CHANGELOG.md` ved ændringer
