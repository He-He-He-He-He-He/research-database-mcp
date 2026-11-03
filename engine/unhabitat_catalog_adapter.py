"""UN-Habitat Urban Indicators Database official search catalog."""
import release_runtime
import requests
BASE = 'https://data.unhabitat.org/api/search/v1/collections/dataset/items'

def search(query, limit=10, start=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('query required (max 200 characters)')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(start, bool) or not isinstance(start, int) or start < 1:
        raise ValueError('start must be at least 1')
    r = requests.get(BASE, params={'q': query.strip(), 'limit': limit, 'startindex': start}, timeout=35)
    r.raise_for_status()
    d = r.json()
    if d.get('type') != 'FeatureCollection' or not isinstance(d.get('features'), list):
        raise ValueError('unexpected catalog response')
    items = []
    for f in d['features']:
        p = f.get('properties', {})
        items.append({'id': f.get('id'), 'title': p.get('title'), 'type': p.get('type'), 'description': p.get('description'), 'snippet': p.get('snippet'), 'license': p.get('licenseInfo'), 'access': p.get('access'), 'url': p.get('url'), 'modified': p.get('modified'), 'tags': p.get('tags')})
    return {'source': 'UN-Habitat Urban Indicators Database', 'query': query.strip(), 'numberMatched': d.get('numberMatched'), 'numberReturned': d.get('numberReturned'), 'start': start, 'items': items, 'note': 'Catalog metadata only; each item may have distinct publisher, license, time coverage, and data access.'}
