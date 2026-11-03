"""UNICEF MICS NADA official survey catalogue metadata, not microdata."""
import release_runtime
import re
import requests
from urllib.parse import urlencode
BASE = 'https://micsnada.unicef.org/index.php/api/catalog'
DOC = 'https://micsnada.unicef.org/index.php/catalog/?tab_type=survey'

def search(keyword='', page=1, limit=20):
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('invalid page')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    p = {'page': page, 'ps': limit}
    if keyword:
        p['sk'] = keyword
    r = requests.get(BASE + '/search', params=p, timeout=45)
    r.raise_for_status()
    j = r.json()
    result = j.get('result')
    if not isinstance(result, dict) or not isinstance(result.get('rows'), list):
        raise ValueError('unexpected catalogue response')
    return {'source': BASE + '/search', 'source_url': BASE + '/search?' + urlencode(p), 'catalog': DOC, 'request': p, 'result': result, 'notes': ['Search is broad across source metadata, not a country-only filter; verify nation and title for each result. Source found is the matched count; total describes the whole catalogue.', 'Catalogue records are survey descriptions, not statistical observations or access to the underlying microdata.', 'Some future planned studies or zero/blank years appear; a record is not proof that a completed survey or accessible data exists.', 'The metadata can link to other repositories; access terms and permission must be checked at each source.']}

def detail(idno):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,150}', idno):
        raise ValueError('invalid study identifier')
    u = BASE + '/' + idno
    r = requests.get(u, timeout=45)
    r.raise_for_status()
    j = r.json()
    if j.get('status') != 'success' or not isinstance(j.get('dataset'), dict):
        raise ValueError('study not found or unavailable')
    return {'source': u, 'catalog': DOC, 'data': j['dataset'], 'note': 'Survey metadata only; verify collection years, source, status and microdata access separately.'}
