"""European Parliament official speech activity metadata by ID."""
import release_runtime
import re
import requests
BASE = 'https://data.europarl.europa.eu/api/v2/speeches'
DOC = 'https://data.europarl.europa.eu/en/developer-corner/opendata-api'

def speech_activity(activity_id):
    if not isinstance(activity_id, str) or not re.fullmatch('MTG-PL-[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Z0-9-]{1,80}', activity_id):
        raise ValueError('Invalid plenary activity ID')
    r = requests.get(BASE + '/' + activity_id, params={'format': 'application/ld+json'}, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('data'), list):
        raise ValueError('Unexpected response shape')
    return {'source_url': r.url, 'documentation': DOC, 'items': d['data'], 'note': 'Official EP activity metadata by exact identifier; not necessarily transcript or translated speech text.'}
