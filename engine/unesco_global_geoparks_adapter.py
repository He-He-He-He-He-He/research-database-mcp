"""UNESCO DataHub Global Geoparks directory."""
import release_runtime
import re
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/eg0001'
FIELDS = 'uuid,ugg_id,title_en,countries,date,area_unit,area_total,population,transnational,coordinates,url'
NOTES = ['This is UNESCO Global Geoparks, a distinct programme from the World Heritage List.', 'The source date field often has January 1 values; do not infer the exact designation day without checking the individual site.', 'Population and area are source values with source units and unspecified measurement dates, not necessarily current; coordinates identify a point rather than boundaries.', 'One site may span multiple countries; country totals cannot be added as unique site counts. Current directory is not a historical snapshot.', 'Dataset description may contain an older headline count than the current API records count; both are preserved. License CC BY-SA 4.0 per UNESCO metadata.']

def _get(url, **kwargs):
    r = requests.get(url, timeout=45, **kwargs)
    r.raise_for_status()
    return r.json()

def search(keyword='', country='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or (not isinstance(country, str)) or (country and (not re.fullmatch('[A-Za-z]{2}', country))) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid search parameters')
    m = _get(BASE)
    meta = m.get('metas', {}).get('default', {})
    rows = []
    total = None
    for n in range(20):
        p = {'select': FIELDS, 'limit': 100, 'offset': 100 * n, 'order_by': 'uuid'}
        if country:
            p['where'] = "countries = '" + country.upper() + "'"
        j = _get(BASE + '/records', params=p)
        if type(j.get('total_count')) is not int or not isinstance(j.get('results'), list):
            raise ValueError('Unexpected UNESCO response')
        if total is None:
            total = j['total_count']
        elif total != j['total_count']:
            raise ValueError('UNESCO results changed during pagination')
        rows.extend(j['results'])
        if len(rows) >= total:
            break
        if not j['results']:
            raise ValueError('Unexpected empty page')
    if len(rows) != total or len({x.get('uuid') for x in rows}) != total:
        raise ValueError('Incomplete or duplicate geoparks')
    if country and any((country.upper() not in (r.get('countries') or []) for r in rows)):
        raise ValueError('Geopark outside requested country')
    rows = [r for r in rows if keyword.casefold() in (r.get('title_en') or '').casefold()]
    return {'source': BASE + '/records', 'page': 'https://data.unesco.org/explore/dataset/eg0001/', 'metadata': {'description': meta.get('description'), 'license': meta.get('license'), 'data_processed': meta.get('data_processed'), 'records_count': meta.get('records_count')}, 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}
