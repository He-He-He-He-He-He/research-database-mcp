"""Read-only Wikidata entity search; community records need source verification."""
import release_runtime
import requests

def search(query, language='en', limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(language, str) or not language.strip():
        raise ValueError('language must be non-empty')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 50):
        raise ValueError('limit must be between 1 and 50')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be non-negative')
    response = requests.get('https://www.wikidata.org/w/api.php', params={'action': 'wbsearchentities', 'search': query, 'language': language, 'format': 'json', 'limit': limit, 'continue': offset, 'type': 'item'}, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (read-only Wikidata entity search)'}, timeout=30)
    response.raise_for_status()
    data = response.json()
    if 'error' in data:
        raise RuntimeError(str(data['error']))
    if not isinstance(data.get('search'), list):
        raise RuntimeError('Unexpected Wikidata response')
    return {'source': 'Wikidata', 'query': query, 'language': language, 'items': data['search'], 'next_offset': data.get('search-continue'), 'note': 'Community-maintained entity records; verify claims against original sources.'}
