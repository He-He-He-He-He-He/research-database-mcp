"""European Parliament public procedure list and detail (not enacted-law text)."""
import release_runtime
import re
import requests
BASE = 'https://data.europarl.europa.eu/api/v2/procedures'
DOC = 'https://data.europarl.europa.eu/en/developer-corner/opendata-api'
FORMAT = 'application/ld+json'

def _get(url, params):
    r = requests.get(url, params=params, timeout=40)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('data'), list):
        raise ValueError('Unexpected European Parliament response')
    return (r, d)

def procedures(limit=10, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 9950):
        raise ValueError('offset must be 0–9950')
    r, d = _get(BASE, {'format': FORMAT, 'limit': limit, 'offset': offset})
    return {'source_url': r.url, 'documentation': DOC, 'source_total_reported': d.get('meta', {}).get('total'), 'items': d['data'], 'note': 'Official EP procedure index; reported total may be capped. No keyword search or completeness guarantee; list may change between pages.'}

def procedure_detail(process_id):
    if not isinstance(process_id, str) or not re.fullmatch('[0-9]{4}-[0-9]{4,6}', process_id):
        raise ValueError('process_id must look like 2024-2511')
    r, d = _get(BASE + '/' + process_id, {'format': FORMAT})
    return {'source_url': r.url, 'documentation': DOC, 'items': d['data'], 'note': 'EP procedure metadata and recorded activities; not authoritative consolidated legislation or all legal developments.'}
