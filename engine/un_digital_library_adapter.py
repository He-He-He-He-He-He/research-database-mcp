"""United Nations Digital Library official Invenio JSON metadata interface."""
import release_runtime
import re
import requests
BASE = 'https://digitallibrary.un.org'
DOC = BASE + '/help/search-engine-api'

def search(query, start=1, limit=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise ValueError('query must be nonempty and at most 300 characters')
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise ValueError('start must be at least 1')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    params = {'ln': 'en', 'p': query.strip(), 'of': 'recjson', 'rg': limit, 'jrec': start}
    r = requests.get(BASE + '/search', params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or len(data) > limit or any((not isinstance(row, dict) for row in data)):
        raise ValueError('unexpected search response or result count')
    return {'source': BASE + '/search', 'documentation': DOC, 'request': params, 'returned': len(data), 'rows': data, 'notes': ['This is catalogue metadata, not a complete full-text search or proof that all linked documents are openly accessible.', 'jrec is one-based. This output does not provide a reliable total; a full page does not guarantee another page.', 'Publication, prepublication and session dates can differ; inspect the individual record and original document before drawing a time-bound conclusion.', 'Availability and reuse rights vary by document; search results can match subjects, authors and other metadata, not only titles.']}

def detail(recid):
    if not isinstance(recid, str) or not re.fullmatch('\\d{1,12}', recid):
        raise ValueError('record ID must contain only digits')
    url = BASE + '/record/' + recid
    r = requests.get(url, params={'of': 'recjson'}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not any((str(x.get('recid')) == recid for x in data if isinstance(x, dict))):
        raise ValueError('record not found or unexpected response')
    return {'source': url, 'documentation': DOC, 'rows': data, 'note': 'Catalogue metadata; check the linked document, dates, availability and reuse conditions separately.'}
