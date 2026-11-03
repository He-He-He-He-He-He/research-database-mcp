"""U.S. BTS monthly transportation services indexes, directly from BTS."""
import release_runtime
import re
import requests
BASE = 'https://data.bts.gov/'
DATA = BASE + 'resource/bw6n-ddqk.json'
META = BASE + 'api/views/bw6n-ddqk.json'
FIELDS = ('obs_date', 'tsi_freight', 'tsi_passenger', 'tsi_total', 'tsi_freight_c', 'tsi_passenger_c', 'tsi_total_c')
NOTES = ['Seasonally adjusted U.S. for-hire transportation services index: monthly average of 2000 = 100. It is an index, not tons, passenger counts, or all transportation.', 'Freight covers for-hire trucking, freight rail, inland waterways, pipelines and air freight; excludes private trucking and international or coastal shipping.', 'Passenger covers local transit, passenger rail and air transport, not private cars, taxis or intercity buses.', 'Index may use proxy series and forecast inputs; observations are subject to revision. The change fields are month-on-month percent changes, not index levels.', 'The current dataset is not a historical publication snapshot. As-of research requires a contemporaneous archived release.']

def _month(s):
    if not isinstance(s, str) or not re.fullmatch('\\d{4}-(0[1-9]|1[0-2])', s):
        raise ValueError('month must be YYYY-MM')
    return s

def query(start, end, limit=100, offset=0):
    start, end = (_month(start), _month(end))
    if start > end or type(limit) is not int or (not 1 <= limit <= 1000) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid range or pagination')
    p = {'$select': ','.join(FIELDS), '$where': f"obs_date >= '{start}-01T00:00:00' AND obs_date <= '{end}-01T00:00:00'", '$order': 'obs_date ASC', '$limit': limit, '$offset': offset}
    r = requests.get(DATA, params=p, timeout=45)
    r.raise_for_status()
    rows = r.json()
    if not isinstance(rows, list):
        raise ValueError('unexpected BTS data response')
    for row in rows:
        if not isinstance(row, dict) or not start <= row.get('obs_date', '')[:7] <= end:
            raise ValueError('BTS row outside requested range')
    r = requests.get(META, timeout=45)
    r.raise_for_status()
    meta = r.json()
    if not isinstance(meta, dict) or meta.get('id') != 'bw6n-ddqk':
        raise ValueError('unexpected BTS metadata')
    columns = {c['fieldName']: c.get('description') for c in meta.get('columns', []) if c.get('fieldName') in FIELDS}
    return {'source': DATA, 'dataset_page': BASE + 'Research-and-Statistics/Transportation-Services-Index-and-Seasonally-Adjus/bw6n-ddqk', 'methodology': 'https://www.bts.gov/learn-about-bts-and-our-work/statistical-methods-and-policies/tsi-frequently-asked-questions', 'rows_updated_at_unix': meta.get('rowsUpdatedAt'), 'source_columns': columns, 'offset': offset, 'limit': limit, 'notes': NOTES, 'records': rows}
