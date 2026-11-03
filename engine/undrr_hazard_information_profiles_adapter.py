"""UNDRR Hazard Information Profiles API, explicit legacy 1.0.0 edition."""
import release_runtime
import requests
URL = 'https://data.undrr.org/api/json/hips/hazards/1.0.0/'
DOC = 'https://data.undrr.org/api/json/'

def _page(page):
    r = requests.get(URL, params={'page': page, 'limit': 100}, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or not isinstance(j.get('data'), list):
        raise ValueError('unexpected response')
    return j

def search(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = []
    expected = None
    pages = None
    for page in range(1, 101):
        j = _page(page)
        try:
            total = int(j['totalCount'])
            n = int(j['totalPages'])
            current = int(j['currentPage'])
        except (KeyError, TypeError, ValueError):
            raise ValueError('missing pagination metadata')
        if current != page or (expected is not None and (total != expected or pages != n)):
            raise ValueError('pagination changed')
        expected = total
        pages = n
        rows.extend(j['data'])
        if page >= pages:
            break
    else:
        raise ValueError('too many pages')
    if len(rows) != expected:
        raise ValueError('incomplete results')
    chosen = [r for r in rows if isinstance(r, dict) and keyword.casefold() in (str(r.get('title', '')) + ' ' + str(r.get('description', ''))).casefold()]
    return {'source': URL, 'documentation': DOC, 'version': '1.0.0', 'dataset_total': expected, 'matched': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'Legacy UNDRR hazard definitions, not event occurrence data or risk assessments. A newer 2.1.0 edition exists and may differ. Descriptions quote external source references; verify latest definition, provenance and third-party rights. Full legacy edition fetched before local keyword filtering.'}
