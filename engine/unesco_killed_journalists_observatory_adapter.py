"""UNESCO Observatory of Killed Journalists public DataHub records."""
import release_runtime
import re
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/fej001'
PAGE = 'https://www.unesco.org/en/safety-journalists/observatory/methodology'
FIELDS = 'id,title_en,countries,country_title_en,date,nationality,gender,enquiry_status,staff,local,conflict_zone,age,media,createdat,updatedat,date_resolution,description_en,dg_request,state_response'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return j

def search(country, start, end, limit=20, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country):
        raise ValueError('country must be two-letter code')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    meta = _get().get('metas', {}).get('default', {})
    params = {'where': f"""countries = "{country}" AND date >= date'{start}-01-01' AND date <= date'{end}-12-31'""", 'select': FIELDS, 'limit': limit, 'offset': offset}
    data = _get('/records', params)
    if not isinstance(data.get('total_count'), int) or not isinstance(data.get('results'), list):
        raise ValueError('unexpected records')
    for r in data['results']:
        if not isinstance(r, dict) or r.get('countries') != country or (not str(r.get('date', ''))[:4].isdigit()) or (not start <= int(r['date'][:4]) <= end):
            raise ValueError('out-of-filter response')
    return {'source': BASE + '/records', 'methodology': PAGE, 'request': params, 'data_modified': meta.get('data_processed'), 'license': meta.get('license'), 'total': data['total_count'], 'offset': offset, 'rows': data['results'], 'note': 'UNESCO monitored and verified cases, not a complete count of all journalist deaths, attacks or proven work-related murders. Country is incident country; retain dates and judicial status as reported, which may be stale or unverified. Case links and state responses are source strings; records selected without geometry. Dataset CC BY-SA 4.0, individual source materials may have other rights.'}
