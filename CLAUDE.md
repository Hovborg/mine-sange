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
| `sw.js` | Service Worker (cache v5) |
| `CHANGELOG.md` | Projekt-changelog med alle ændringer |

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

## Tilføj ny sang — hvad skal du bruge?

For at tilføje en ny sang til siden, skal følgende leveres:

1. **MP3-fil** — Selve sangen i MP3-format. Placeres i `/audio/` (f.eks. `audio/sang-navn.mp3`)
2. **Cover art** — Billede i SVG eller PNG-format. Placeres i `/audio/` (f.eks. `audio/sang-navn-art.svg`)
3. **Sangtitel** — Titel som vises i UI
4. **Sang-id** — Kort kebab-case id (f.eks. `min-nye-sang`)
5. **Varighed** — Sangens længde i sekunder (heltal)
6. **Gradient-farver** — 3 farver til baggrunds-gradient (f.eks. `#f59e0b, #d97706, #92400e`)
7. **Glow-farve** — Primær farve til glow-effekt (f.eks. `#f59e0b`)
8. **Lyrics med timestamps** — Word-by-word timing i formatet:
   ```
   {t: start_sek, text: "Hele linjen", w: [ord1_start, ord2_start, ...]}
   ```
   Genereres bedst med `stable-ts` forced alignment
9. **(Valgfrit) Subtitle** — Undertitel/artist-navn

### Filer der skal opdateres:
- **HTML-fil** (index.html, hitboxen.html, etc.) — Tilføj sang-objekt til `songs[]` array
- **sw.js** — Tilføj MP3 og art til `PRECACHE[]` listen, bump cache version
- **sang-stats.py** — Tilføj sang-id til `VALID_SONGS` set
- **admin.html** — Tilføj sang til `SONG_COLORS` og `SONG_NAMES`

## Hosting & Drift
- Hostet på **GitHub Pages** — pusher til `main` deployer automatisk
- **Ingen lokal server nødvendig** for selve websiden
- `sang-stats.py` kører på serveren med nginx logs (ikke lokal PC)
- Service Worker opdateres automatisk i besøgendes browsere når ny version pushes
- Ved PC-genstart: Ingen lokal proces behøver genstartes — alt kører i skyen

## Sangrækkefølge (index.html)
1. En Fars Kamp for Sine Børn
2. KRISTOFFER!
3. Som en Kokosnød
4. Mine Drenge
5. Bare En Far
6. Stop Så Brian
7. Brormand
8. Hvad Børn Ved
9. Hjem
10. Lad Dem Snakke
11. I Nat
12. Godnat, Skam

## Vigtigt
- Rør IKKE lyrics timestamps medmindre specifikt bedt om det
- Behold Google Cast og AirPlay integration
- Test altid at service worker cache-listen matcher faktiske filer
- `og-image.png` bruges til social sharing
- Opdater altid `CHANGELOG.md` ved ændringer
