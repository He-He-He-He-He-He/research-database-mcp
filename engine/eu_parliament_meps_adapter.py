"""European Parliament public member list and person detail metadata."""
import release_runtime
import re
import requests
BASE = 'https://data.europarl.europa.eu/api/v2/meps'
DOC = 'https://data.europarl.europa.eu/en/developer-corner/opendata-api'

def _get(url, params):
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    if len(r.content) > 8000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('data'), list):
        raise ValueError('Unexpected response shape')
    return {'source_url': r.url, 'documentation': DOC, 'items': d['data'], 'note': 'European Parliament public member metadata; list includes former members. Consult dated memberships to assess current status.'}

def members(limit=10, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 9950):
        raise ValueError('offset must be 0–9950')
    return _get(BASE, {'format': 'application/ld+json', 'limit': limit, 'offset': offset})

def member_detail(person_id):
    if not isinstance(person_id, str) or not re.fullmatch('[0-9]{1,9}', person_id) or int(person_id) == 0:
        raise ValueError('person_id must be positive numeric ID')
    return _get(BASE + '/' + person_id, {'format': 'application/ld+json'})
