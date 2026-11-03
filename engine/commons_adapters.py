"""Wikimedia Commons public media search with per-file licensing metadata."""
import release_runtime
import requests

def search(query, size=5, continuation=None):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 10):
        raise ValueError('size must be between 1 and 10')
    params = {'action': 'query', 'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': query, 'gsrlimit': size, 'prop': 'imageinfo', 'iiprop': 'url|mime|extmetadata', 'iiextmetadatafilter': 'LicenseShortName|LicenseUrl|UsageTerms|Artist|Credit', 'format': 'json', 'formatversion': 2}
    if continuation is not None:
        if not isinstance(continuation, dict) or not set(continuation) <= {'continue', 'gsroffset'}:
            raise ValueError('invalid continuation')
        params.update(continuation)
    r = requests.get('https://commons.wikimedia.org/w/api.php', params=params, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (read-only Commons search)'}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if 'error' in data:
        raise RuntimeError(str(data['error']))
    pages = data.get('query', {}).get('pages', [])
    return {'source': 'Wikimedia Commons', 'query': query, 'items': pages, 'continuation': data.get('continue'), 'note': 'Check each file page and license, including attribution and reuse conditions.'}
