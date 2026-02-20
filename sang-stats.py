#!/usr/bin/env python3
"""Parse nginx access logs for sang.hovborg.tech and generate stats JSON."""
import re
import json
import os
import time
from datetime import datetime
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.error import URLError

try:
    from user_agents import parse as parse_ua
    HAS_UA = True
except ImportError:
    HAS_UA = False

LOG_FILE = '/var/log/nginx/sang_access.log'
NP_LOG_FILE = '/var/www/sang/admin/np.log'
TRACK_LOG_FILE = '/var/www/sang/admin/track.log'
OUTPUT_FILE = '/var/www/sang/admin/stats.json'
GEO_CACHE_FILE = '/var/www/sang/admin/geo_cache.json'

# Valid song IDs (whitelist for track events)
VALID_SONGS = {
    'bare-en-far', 'kristoffer', 'kokosnoed', 'mine-drenge',
    'fars-kamp', 'stop-brian', 'brormand',
    'en-fars-kamp', 'stop-saa-brian', 'som-en-kokosnoed',
}

BOT_PATTERNS = re.compile(r'bot|crawl|spider|slurp|mediapartners|adsbot|bingpreview|googlebot|yandex|baidu|semrush|ahrefs|mj12bot|dotbot|searchbot|claudebot', re.I)

# Map short heartbeat IDs to canonical audio file names
NP_SONG_MAP = {
    'fars-kamp': 'en-fars-kamp',
    'stop-brian': 'stop-saa-brian',
    'kokosnoed': 'som-en-kokosnoed',
}

LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) - \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<bytes>\d+) "(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)

def parse_time(time_str):
    try:
        dt = datetime.strptime(time_str.split(' ')[0], '%d/%b/%Y:%H:%M:%S')
        return dt.isoformat() + 'Z'
    except Exception:
        return time_str

def parse_song_name(path):
    m = re.match(r'/audio/(.+)\.mp3', path)
    if m:
        return m.group(1)
    return None

def get_device_info(ua_str):
    """Parse UA string into device/browser/os info."""
    if not HAS_UA or not ua_str:
        return {'device': 'Ukendt', 'browser': '', 'os': ''}
    try:
        ua = parse_ua(ua_str)
        device = 'Mobil' if ua.is_mobile else 'Tablet' if ua.is_tablet else 'PC' if ua.is_pc else 'Bot' if ua.is_bot else 'Ukendt'
        browser = ua.browser.family or ''
        os_name = ua.os.family or ''
        return {'device': device, 'browser': browser, 'os': os_name}
    except Exception:
        return {'device': 'Ukendt', 'browser': '', 'os': ''}

# --- GeoIP via ip-api.com (free, no account needed) ---
def load_geo_cache():
    if os.path.exists(GEO_CACHE_FILE):
        try:
            with open(GEO_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_geo_cache(cache):
    try:
        with open(GEO_CACHE_FILE, 'w') as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass

def is_private_ip(ip):
    """Check if IP is private/local."""
    if ip.startswith(('127.', '10.', '192.168.')):
        return True
    if ip.startswith('172.'):
        try:
            second = int(ip.split('.')[1])
            if 16 <= second <= 31:
                return True
        except Exception:
            pass
    if ip in ('::1', '') or ip.startswith('fe80:'):
        return True
    return False

def lookup_countries(ips, cache):
    """Look up countries for IPs not in cache. Uses ip-api.com batch endpoint."""
    new_ips = [ip for ip in ips if ip not in cache and not is_private_ip(ip)]
    if not new_ips:
        return cache

    # ip-api.com batch: POST up to 100 IPs at a time
    for i in range(0, len(new_ips), 100):
        batch = new_ips[i:i+100]
        try:
            payload = json.dumps([{"query": ip, "fields": "country,countryCode,query"} for ip in batch]).encode()
            req = Request('http://ip-api.com/batch', data=payload, headers={'Content-Type': 'application/json'})
            with urlopen(req, timeout=5) as resp:
                results = json.loads(resp.read())
                for r in results:
                    ip = r.get('query', '')
                    country = r.get('country', 'Ukendt')
                    code = r.get('countryCode', '')
                    cache[ip] = {'country': country, 'code': code}
        except Exception:
            break
        time.sleep(0.5)  # respect rate limits

    # Mark private IPs
    for ip in ips:
        if ip not in cache and is_private_ip(ip):
            cache[ip] = {'country': 'Lokalt', 'code': 'LO'}

    return cache

def main():
    plays = []
    per_song = defaultdict(int)
    per_ip = defaultdict(int)
    per_hour = defaultdict(int)
    per_day = defaultdict(int)
    per_browser = defaultdict(int)
    per_os = defaultdict(int)
    per_device = defaultdict(int)
    per_country = defaultdict(int)
    page_views = 0
    unique_page_ips = set()
    hourly_activity = defaultdict(int)  # hour of day -> count

    if not os.path.exists(LOG_FILE):
        return

    all_ips = set()

    with open(LOG_FILE, 'r') as f:
        for line in f:
            m = LOG_PATTERN.match(line)
            if not m:
                continue

            ip = m.group('ip')
            time_str = m.group('time')
            method = m.group('method')
            path = m.group('path')
            status = int(m.group('status'))
            bytes_sent = int(m.group('bytes'))
            ua = m.group('ua')

            if BOT_PATTERNS.search(ua):
                continue

            # Count page views
            if method == 'GET' and path == '/' and status == 200:
                page_views += 1
                unique_page_ips.add(ip)

            # Audio plays
            if method != 'GET' or status not in (200, 206):
                continue

            song = parse_song_name(path)
            if not song or '-art' in song:
                continue

            all_ips.add(ip)
            parsed_time = parse_time(time_str)
            day_key = parsed_time[:10]

            # Hour of day for activity heatmap
            try:
                hour = int(parsed_time[11:13])
                hourly_activity[hour] += 1
            except Exception:
                pass

            # Device/browser/os stats
            info = get_device_info(ua)
            per_browser[info['browser']] += 1
            per_os[info['os']] += 1
            per_device[info['device']] += 1

            plays.append({
                't': parsed_time,
                'ip': ip,
                's': song,
                'ua': ua[:120],
                'device': info['device'],
                'browser': info['browser'],
                'os': info['os']
            })

            per_song[song] += 1
            per_ip[ip] += 1
            per_day[day_key] += 1

    # --- Also count plays from np.log (catches SW-cached plays) ---
    # Build set of known plays (ip+song+minute) from nginx log to avoid duplicates
    known_plays = set()
    for p in plays:
        known_plays.add((p['ip'], p['s'], p['t'][:16]))  # ip+song+minute

    if os.path.exists(NP_LOG_FILE):
        # Track sessions: (ip, song) -> last_seen_timestamp
        np_sessions = {}
        np_entries = []
        with open(NP_LOG_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) < 3:
                    continue
                ip = parts[0].strip()
                time_str = parts[1].strip()
                song = parts[2].strip()
                song = NP_SONG_MAP.get(song, song)  # normalize short IDs
                # Format: IP|time|song|duration|ua (new) or IP|time|song|ua (old)
                if len(parts) >= 5:
                    ua = parts[4].strip()
                elif len(parts) >= 4:
                    ua = parts[3].strip()
                else:
                    ua = ''
                if not song or song == '-':
                    continue
                if BOT_PATTERNS.search(ua):
                    continue
                try:
                    ts = datetime.fromisoformat(time_str.replace('+00:00', '+00:00').replace('Z', '+00:00'))
                    ts_utc = ts.replace(tzinfo=None)
                except Exception:
                    continue
                key = (ip, song)
                iso = ts_utc.isoformat() + 'Z'
                # New session if >30s gap from last heartbeat for this ip+song
                if key in np_sessions:
                    last_ts = np_sessions[key]
                    diff = (ts_utc - last_ts).total_seconds()
                    if diff > 30:
                        np_entries.append((ip, song, iso, ua, ts_utc))
                else:
                    np_entries.append((ip, song, iso, ua, ts_utc))
                np_sessions[key] = ts_utc

        # Add np plays that aren't already in nginx log
        for ip, song, iso, ua, ts_utc in np_entries:
            minute_key = iso[:16]
            if (ip, song, minute_key) in known_plays:
                continue
            known_plays.add((ip, song, minute_key))
            all_ips.add(ip)
            day_key = iso[:10]
            info = get_device_info(ua)
            per_browser[info['browser']] += 1
            per_os[info['os']] += 1
            per_device[info['device']] += 1
            plays.append({
                't': iso, 'ip': ip, 's': song, 'ua': ua[:120],
                'device': info['device'], 'browser': info['browser'], 'os': info['os']
            })
            per_song[song] += 1
            per_ip[ip] += 1
            per_day[day_key] += 1
            try:
                hour = int(iso[11:13])
                hourly_activity[hour] += 1
            except Exception:
                pass

    # --- Parse track.log for explicit play/end/leave events ---
    # Format: IP|timestamp|event|song|duration|useragent
    per_song_duration = defaultdict(float)  # song -> total listen seconds
    total_listen_time = 0.0
    track_plays_added = 0

    if os.path.exists(TRACK_LOG_FILE):
        with open(TRACK_LOG_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) < 5:
                    continue
                ip = parts[0].strip()
                time_str = parts[1].strip()
                event = parts[2].strip()
                song = parts[3].strip()
                dur_str = parts[4].strip()
                ua = parts[5].strip() if len(parts) > 5 else ''

                if not song or song == '-' or song not in VALID_SONGS:
                    continue
                if BOT_PATTERNS.search(ua):
                    continue

                song = NP_SONG_MAP.get(song, song)  # normalize

                # Only count 'play' events as new plays
                if event != 'play':
                    # But track duration from end/leave events
                    if event in ('end', 'leave', 'pause'):
                        try:
                            dur = float(dur_str)
                            if 0 < dur < 600:  # sanity: max 10 min
                                per_song_duration[song] += dur
                                total_listen_time += dur
                        except Exception:
                            pass
                    continue

                try:
                    ts = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    ts_utc = ts.replace(tzinfo=None)
                except Exception:
                    continue

                iso = ts_utc.isoformat() + 'Z'
                minute_key = iso[:16]

                # Deduplicate against existing plays
                if (ip, song, minute_key) in known_plays:
                    continue
                known_plays.add((ip, song, minute_key))

                all_ips.add(ip)
                day_key = iso[:10]
                info = get_device_info(ua)
                per_browser[info['browser']] += 1
                per_os[info['os']] += 1
                per_device[info['device']] += 1
                plays.append({
                    't': iso, 'ip': ip, 's': song, 'ua': ua[:120],
                    'device': info['device'], 'browser': info['browser'], 'os': info['os']
                })
                per_song[song] += 1
                per_ip[ip] += 1
                per_day[day_key] += 1
                track_plays_added += 1
                try:
                    hour = int(iso[11:13])
                    hourly_activity[hour] += 1
                except Exception:
                    pass

    # GeoIP lookup
    geo_cache = load_geo_cache()
    geo_cache = lookup_countries(all_ips | unique_page_ips, geo_cache)
    save_geo_cache(geo_cache)

    # Count countries
    for ip in per_ip:
        geo = geo_cache.get(ip, {})
        country = geo.get('country', 'Ukendt')
        per_country[country] += per_ip[ip]

    # Add country to recent plays
    for play in plays:
        geo = geo_cache.get(play['ip'], {})
        play['country'] = geo.get('country', 'Ukendt')
        play['cc'] = geo.get('code', '')

    plays.sort(key=lambda x: x['t'], reverse=True)
    top_ips = sorted(per_ip.items(), key=lambda x: x[1], reverse=True)[:20]

    # Calculate average plays per day
    total_days = max(len(per_day), 1)
    avg_per_day = round(len(plays) / total_days, 1)

    # Peak hour
    peak_hour = max(hourly_activity, key=hourly_activity.get) if hourly_activity else 0

    # Format listen time
    total_listen_mins = round(total_listen_time / 60, 1)

    stats = {
        'generated': datetime.utcnow().isoformat() + 'Z',
        'total_plays': len(plays),
        'unique_listeners': len(per_ip),
        'page_views': page_views,
        'unique_visitors': len(unique_page_ips),
        'avg_plays_per_day': avg_per_day,
        'peak_hour': peak_hour,
        'total_listen_minutes': total_listen_mins,
        'per_song_duration': {k: round(v / 60, 1) for k, v in sorted(per_song_duration.items(), key=lambda x: x[1], reverse=True)},
        'per_song': dict(sorted(per_song.items(), key=lambda x: x[1], reverse=True)),
        'per_day': dict(sorted(per_day.items())),
        'hourly_activity': {str(h): hourly_activity.get(h, 0) for h in range(24)},
        'per_browser': dict(sorted(per_browser.items(), key=lambda x: x[1], reverse=True)[:10]),
        'per_os': dict(sorted(per_os.items(), key=lambda x: x[1], reverse=True)[:10]),
        'per_device': dict(sorted(per_device.items(), key=lambda x: x[1], reverse=True)),
        'per_country': dict(sorted(per_country.items(), key=lambda x: x[1], reverse=True)[:15]),
        'top_ips': [{'ip': ip, 'plays': count, 'country': geo_cache.get(ip, {}).get('country', '?')} for ip, count in top_ips],
        'recent_plays': plays[:200]
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False)

if __name__ == '__main__':
    main()
