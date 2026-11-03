"""Historical World Bank Sustainable Energy for All source 35."""
import release_runtime
import re, requests
BASE = 'https://api.worldbank.org/v2/sources/35/'
NOTE = 'Historical source 35 API last returned an update date of 2018-06-30; it may differ from the newer catalog description. Access estimates can include modelled or assumed values; observation API does not identify the method for each value. Units vary by indicator: consult its metadata. Null means missing, not zero; this dataset is not necessarily current.'

def get(path):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 500, 'page': 1}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or data not found')
    if not isinstance(j, dict) or j.get('pages') != 1:
        raise ValueError('unexpected or paginated World Bank response')
    return (j, r.url)

def catalog(kind, keyword=''):
    if kind not in ('country', 'series') or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid catalog query')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    out = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'total': j['total'], 'records': out, 'note': NOTE}

def metadata(indicator):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9._]{1,100}', indicator):
        raise ValueError('invalid indicator')
    j, u = get('series/' + indicator + '/metadata')
    v = j['source'][0]['concept'][0]['variable'][0]
    if v['id'] != indicator:
        raise ValueError('unexpected indicator')
    return {'source': u, 'indicator': indicator, 'metadata': v['metatype'], 'note': NOTE}

def observations(country, indicator, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9]{3}', country):
        raise ValueError('invalid country')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9._]{1,100}', indicator):
        raise ValueError('invalid indicator')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    j, u = get(f'country/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '35' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected observations')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        year = int(dims['Time']['name'])
        if dims['Country']['code'] != country or dims['Series']['code'] != indicator:
            raise ValueError('unexpected observation dimensions')
        if start <= year <= end:
            out.append({'year': year, 'raw_value': x['value'], 'dimensions': dims})
    return {'source': u, 'last_updated': j.get('lastupdated'), 'records': out, 'note': NOTE}
