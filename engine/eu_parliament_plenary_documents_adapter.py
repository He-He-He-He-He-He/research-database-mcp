"""European Parliament official plenary document metadata, list and detail."""
import release_runtime
import re
import requests
BASE = 'https://data.europarl.europa.eu/api/v2/plenary-documents'
DOC = 'https://data.europarl.europa.eu/en/developer-corner/opendata-api'
FORMAT = 'application/ld+json'

def _get(url, params):
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    if len(r.content) > 8000000:
        raise ValueError('Unexpected response size')
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get('data'), list):
        raise ValueError('Unexpected response shape')
    return {'source_url': r.url, 'documentation': DOC, 'items': data['data'], 'note': 'European Parliament plenary document metadata. Document links and language versions are source-provided; no full text fetched. Not a consolidated law database.'}

def plenary_documents(limit=10, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 9950):
        raise ValueError('offset must be 0–9950')
    return _get(BASE, {'format': FORMAT, 'limit': limit, 'offset': offset})

def plenary_document_detail(document_id):
    if not isinstance(document_id, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9-]{2,99}', document_id):
        raise ValueError('Invalid document identifier')
    return _get(BASE + '/' + document_id, {'format': FORMAT})
