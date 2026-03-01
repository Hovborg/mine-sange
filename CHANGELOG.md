# Changelog — Fars Jukebox

Alle bemærkelsesværdige ændringer i dette projekt dokumenteres her.

## 2026-03-01

### Sangrækkefølge
- Bare En Far flyttet til plads 5 i sanglisten

### Sikkerhed & Fixes (53 issues)
- Admin login-overlay med SHA-256 autentificering (sessionStorage)
- XSS-fix i admin: inline onclick erstattet med data-attributes + event delegation
- 5 manglende sange tilføjet til admin SONG_COLORS/SONG_NAMES
- 10 manglende sange tilføjet til sang-stats.py VALID_SONGS
- Deprecated `datetime.utcnow()` erstattet med `datetime.now(timezone.utc)`
- Atomic file write i sang-stats.py (tempfile + os.replace)
- Progress bar touch fix: passive:false + preventDefault for scrub
- Mousemove scrub throttlet med requestAnimationFrame
- CSS `--modal-tint` variabel taget i brug i @supports fallback
- Godnat Skam lyrics tilføjet til index.html

### Tilgængelighed
- Skip-links tilføjet til hitboxen.html og kristoffer.html
- Udvidede keyboard shortcuts: ArrowUp/Down (volume), P (prev), M (mute), Escape (luk)
- Søgebar tilføjet til hitboxen.html
- 4. animation delay til song cards i hitboxen

### Projektfiler
- CLAUDE.md opdateret med komplet projektdokumentation og sang-guide
- SW cache bumpet v2 → v4 med 14 nye precache-entries
- Søgebar, sleep timer og accessibility forbedringer (bba2e64)

## 2026-02-22

### Hit-Boxen
- Ny side: hitboxen.html med 3 sange og word-by-word karaoke lyrics
- Giv Os Mere tilføjet med stable-ts timestamps og cover art
- I alt 4 sange på Hit-Boxen: Giv Os Mere, Lige Om Lidt, Højere, Min Tur

### Lyrics & Sync
- Lyrics sync fixet med stable-ts forced alignment for 7 sange
- Fix: particleEls temporal dead zone crash der ødelagde sanglisten

## 2026-02-21

### Bug Fixes
- 13 bugs og UX-issues fixet på tværs af index.html og kristoffer.html

## 2026-02-20

### Design
- Spotify/Apple Music redesign med 3D-logo og nye sange
- Transparent 3D-logo og forbedret mørk baggrund

## 2026-02-17

### Grundlæggende Platform
- Fars Jukebox lanceret som musikdelingsside
- Sangsiden oprettet med global play-tæller
- Modal player med album art for hver sang
- Custom domain: sang.hovborg.tech (GitHub Pages + CNAME)
- HTML5 audio player med autoplay (erstattede iframe)
- Audio-filer hostet lokalt (fjernede Google Drive-afhængighed)
- Professionelt redesign med premium musikapp-æstetik
- Fix: sang-til-link mapping baseret på verificeret filindhold
