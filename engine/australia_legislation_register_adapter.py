"""Australia Federal Register of Legislation public API title and version records."""
import release_runtime
import requests
from urllib.parse import urlencode
BASE = 'https://api.prod.legislation.gov.au/v1/'

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=40, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('value'), list):
        raise ValueError('Unexpected legislation API response')
    return {**data, 'toolkit_source_url': BASE + path + '?' + urlencode(params), 'toolkit_note': 'Official title/version metadata, not a complete legal opinion. Verify commencement, amendments and status; source updates can change cross-page ordering.'}

def _paging(limit, offset):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('limit must be 1–100 and offset must be nonnegative')
    return {'$top': limit, '$skip': offset}

def search_titles(name, limit=10, offset=0, in_force=None):
    if not isinstance(name, str) or not name.strip():
        raise ValueError('name must be nonempty')
    name = name.strip().replace("'", "''")
    f = "contains(name,'" + name + "')"
    if in_force is not None:
        if not isinstance(in_force, bool):
            raise ValueError('in_force must be boolean or None')
        f += ' and isInForce eq ' + str(in_force).lower()
    params = _paging(limit, offset)
    params['$filter'] = f
    return _get('titles', params)

def versions(title_id, limit=10, offset=0):
    if not isinstance(title_id, str) or not title_id.strip():
        raise ValueError('title_id must be nonempty')
    title_id = title_id.strip().replace("'", "''")
    params = _paging(limit, offset)
    params['$filter'] = "titleId eq '" + title_id + "'"
    return _get('versions', params)
