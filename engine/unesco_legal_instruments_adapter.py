"""UNESCO DataHub legal instruments and currently listed ratification codes."""
import release_runtime
import re
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/la0001'
FIELDS = 'id,uuid,title_en,date,type,theme,countries_ratification,entry_en,depositary_en,updatedat,website_en'
NOTES = ['The instrument date is not a country ratification or entry-into-force date. The current countries_ratification list has no country-specific ratification dates.', 'Current membership and status may have changed; this dataset is not a historical status snapshot. Confirm deposits, reservations, amendments and current legal effect against the official depositary.', 'Treaty, declaration and recommendation have different legal effects. A listing alone does not establish compliance or applicability.', 'UNESCO dataset metadata lists CC BY-SA 4.0; source documents may have their own terms.']

def _get(url, **kwargs):
    r = requests.get(url, timeout=45, **kwargs)
    r.raise_for_status()
    return r.json()

def search(keyword='', country='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or (not isinstance(country, str)) or (country and (not re.fullmatch('[A-Za-z]{2}', country))) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid search parameters')
    meta = _get(BASE)
    default = meta.get('metas', {}).get('default', {})
    allrows = []
    page = 0
    total = None
    while True:
        data = _get(BASE + '/records', params={'select': FIELDS, 'order_by': 'uuid', 'limit': 100, 'offset': page * 100})
        if not isinstance(data, dict) or not isinstance(data.get('results'), list) or type(data.get('total_count')) is not int:
            raise ValueError('Unexpected UNESCO result')
        if total is None:
            total = data['total_count']
        elif total != data['total_count']:
            raise ValueError('UNESCO dataset changed during pagination; retry')
        if total > 2000:
            raise ValueError('UNESCO dataset exceeds safe page limit')
        allrows.extend(data['results'])
        if len(allrows) >= total:
            break
        if not data['results']:
            raise ValueError('Unexpected empty UNESCO page')
        page += 1
    if len(allrows) != total or len({r.get('uuid') for r in allrows}) != total:
        raise ValueError('Incomplete or duplicate UNESCO data')
    term = keyword.casefold()
    country = country.upper()
    rows = [r for r in allrows if term in (str(r.get('title_en') or '') + ' ' + str(r.get('theme') or '')).casefold() and (not country or country in (r.get('countries_ratification') or []))]
    return {'source': BASE + '/records', 'page': 'https://data.unesco.org/explore/dataset/la0001/', 'metadata': {'title': default.get('title'), 'license': default.get('license'), 'data_processed': default.get('data_processed')}, 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}
