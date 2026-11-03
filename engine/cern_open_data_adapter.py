"""CERN Open Data Portal official dataset metadata API."""
import release_runtime
import re
import requests
BASE = 'https://opendata.cern.ch/api/records/'
NOTES = ["A catalogue record is not necessarily a fully online dataset: inspect availability, file access methods and each record's license and attribution.", 'Creation, update and publication dates refer to different events; record migration or later edits can make them differ. Current metadata is not automatically a historical snapshot.', 'Experimental, simulated and education datasets have different meanings; inspect the experiment, dataset type, methodology and validation before using results.', 'Files may be large or use specialised root:// transport. This interface returns metadata only and does not download underlying data.']

def _get(url, params=None):
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('Unexpected CERN response')
    return j

def search(keyword, limit=5, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or (type(limit) is not int) or (not 1 <= limit <= 30) or (type(page) is not int) or (not 1 <= page <= 100):
        raise ValueError('Invalid CERN query')
    j = _get(BASE, {'q': keyword, 'size': limit, 'page': page})
    h = j.get('hits')
    if not isinstance(h, dict) or not isinstance(h.get('hits'), list) or type(h.get('total')) is not int or (len(h['hits']) > limit):
        raise ValueError('Unexpected CERN search response')
    return {'source': BASE, 'query': keyword, 'page': page, 'total_matching': h['total'], 'next': j.get('links', {}).get('next'), 'notes': NOTES, 'records': h['hits']}

def record(record_id):
    if not re.fullmatch('[0-9]{1,12}', str(record_id)):
        raise ValueError('Invalid CERN record ID')
    j = _get(BASE + str(record_id))
    if str(j.get('id')) != str(record_id) or not isinstance(j.get('metadata'), dict):
        raise ValueError('Unexpected CERN record')
    return {'source': BASE + str(record_id), 'page': 'https://opendata.cern.ch/record/' + str(record_id), 'notes': NOTES, 'record': j}
