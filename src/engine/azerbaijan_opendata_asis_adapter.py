"""Azerbaijan government open data catalog and State Statistical Committee ASIS data."""
import release_runtime
import re
import requests
CAT = 'https://admin.opendata.az/api/3/action/package_search'
ASIS = 'https://www.azstat.gov.az/AsisOpenDataApi/data'

def _json(url, params, maxbytes=5000000):
    with requests.get(url, params=params, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > maxbytes:
                raise ValueError('Response too large')
    import json
    return json.loads(raw.decode('utf-8-sig'))

def search(query='', limit=10, offset=0):
    if not isinstance(query, str) or len(query) > 200 or type(limit) is not int or (not 1 <= limit <= 50) or (type(offset) is not int) or (not 0 <= offset <= 10000):
        raise ValueError('Invalid search or pagination')
    j = _json(CAT, {'q': query, 'rows': limit, 'start': offset})
    if not j.get('success'):
        raise ValueError('Catalog search failed')
    return {'source': CAT, 'query': query, 'result': j['result'], 'notes': ['Search covers the government portal, not only the State Statistical Committee; provider and license vary by dataset.', 'Resource URLs and metadata are returned, but availability and license must be checked individually.']}

def data(table_id, language='en', period='', limit=100):
    if not isinstance(table_id, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', table_id) or language not in ('en', 'az', 'ru') or (not isinstance(period, str)) or (len(period) > 40) or (type(limit) is not int) or (not 1 <= limit <= 1000):
        raise ValueError('Invalid table ID, language, period or limit')
    params = {'table_id': table_id, 'lang': language}
    j = _json(ASIS, params)
    if not j.get('success') or not isinstance(j.get('data'), list):
        raise ValueError('ASIS returned no successful data')
    if j.get('count') != len(j['data']):
        raise ValueError('Upstream count differs from returned data')
    matches = [x for x in j['data'] if not period or str(x.get('period')) == period]
    return {'source': ASIS, 'params': params, 'table': j.get('table'), 'source_count': j['count'], 'period_filter': period, 'matched_count': len(matches), 'returned': min(limit, len(matches)), 'records': matches[:limit], 'notes': ['Original units, hierarchy, period type, missing symbols, comments and publication-status fields are retained; their meaning must be checked against source methodology.', 'Period filtering occurs locally after retrieving the complete bounded response; returned rows may be limited.', 'Current data can be revised and is not proof of historical availability.']}
