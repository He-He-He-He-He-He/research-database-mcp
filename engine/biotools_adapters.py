"""ELIXIR bio.tools public registry search for life-science software."""
import release_runtime
import requests

def search(query, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('page must be a positive integer')
    r = requests.get('https://bio.tools/api/tool/', params={'q': query, 'format': 'json', 'page': page}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('list'), list) or 'count' not in data:
        raise RuntimeError('Unexpected bio.tools response')
    return {'source': 'bio.tools', 'query': query, 'page': page, 'total': data['count'], 'items': data['list'], 'next': data.get('next'), 'note': 'Registry metadata under CC BY 4.0; individual software has its own license and availability.'}
