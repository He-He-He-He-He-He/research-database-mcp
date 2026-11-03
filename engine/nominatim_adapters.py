"""Nominatim user-triggered geocoding; no bulk or autocomplete use."""
import release_runtime
import fcntl
import os
import tempfile
import time
import requests
_cache = {}

def search(query, limit=5):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('limit must be 1 to 10')
    key = (query, limit)
    if key in _cache:
        return _cache[key]
    lock_path = os.path.join(tempfile.gettempdir(), 'zju-research-nominatim.lock')
    with open(lock_path, 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        lock.seek(0)
        try:
            last = float(lock.read().strip() or '0')
        except ValueError:
            last = 0
        delay = 1.1 - (time.time() - last)
        if delay > 0:
            time.sleep(delay)
        lock.seek(0)
        lock.truncate()
        lock.write(str(time.time()))
        lock.flush()
        endpoint = 'https://nominatim.openstreetmap.org/search'
        r = requests.get(endpoint, params={'q': query, 'format': 'jsonv2', 'limit': limit}, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (personal research geocoding)'}, timeout=30)
        r.raise_for_status()
        rows = r.json()
        if not isinstance(rows, list):
            raise RuntimeError('Unexpected Nominatim response')
    result = {'source': 'OpenStreetMap Nominatim', 'query': query, 'items': rows, 'attribution': '© OpenStreetMap contributors; ODbL', 'note': 'Candidates can be wrong or ambiguous; verify names and coordinates. User-triggered searches only; no autocomplete or bulk geocoding.'}
    _cache[key] = result
    return result
