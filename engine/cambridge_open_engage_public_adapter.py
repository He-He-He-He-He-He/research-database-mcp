"""Cambridge Open Engage public API: bounded early-research metadata."""
import release_runtime
import re
import requests
BASE = 'https://www.cambridge.org/engage/coe/public-api/v1/'

def _brief(i):
    keys = ('id', 'doi', 'title', 'contentType', 'subject', 'status', 'publishedDate', 'version', 'isLatestVersion', 'authors', 'license', 'vor')
    return {k: i.get(k) for k in keys}

def search(term, offset=0, limit=5, timeout=20):
    if not isinstance(term, str) or not term.strip() or len(term) > 100:
        raise ValueError('term must contain 1 to 100 characters')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 5000):
        raise ValueError('offset must be from 0 to 5000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be from 1 to 20')
    r = requests.get(BASE + 'items', params={'term': term.strip(), 'skip': offset, 'limit': limit}, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('totalCount'), int) or not isinstance(d.get('itemHits'), list):
        raise ValueError('unexpected response')
    items = [_brief(x['item']) for x in d['itemHits'] if isinstance(x, dict) and isinstance(x.get('item'), dict)]
    return {'source': 'Cambridge Open Engage public API', 'term': term.strip(), 'offset': offset, 'limit': limit, 'total': d['totalCount'], 'items': items, 'note': '早期研究成果，可能未经同行评议；不等同 Cambridge Core 馆藏。'}

def detail(item_id, timeout=20):
    if not isinstance(item_id, str) or not re.fullmatch('[0-9a-fA-F]{24}', item_id):
        raise ValueError('item_id must be a 24-character hexadecimal ID')
    r = requests.get(BASE + 'items/' + item_id, timeout=timeout)
    r.raise_for_status()
    i = r.json()
    if not isinstance(i, dict) or i.get('id') != item_id:
        raise ValueError('unexpected detail response')
    return {'source': 'Cambridge Open Engage public API', 'item': _brief(i), 'note': '早期研究成果，不等同 Cambridge Core 馆藏。'}
