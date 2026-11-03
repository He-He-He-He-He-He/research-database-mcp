"""World Bank 2014 Gender Disaggregated Labor Database, source 80."""
import release_runtime
import re, requests
BASE = 'https://api.worldbank.org/v2/sources/80/'
NOTE = '2014 historical harmonized/modelled data, not a current survey or national total; sector and education categories matter. Some series names state %, but four gender/skill shares for Egypt AFS sum to approximately 1; scale is ambiguous, so values are unchanged and not automatically multiplied. Consult original methodology for interpretation. Empty/null is not zero. The API reports metadata unavailable.'

def get(path):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 500, 'page': 1}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or data not found')
    if not isinstance(j, dict) or j.get('pages') != 1:
        raise ValueError('unexpected or paginated response')
    return (j, r.url)

def catalog(kind, keyword=''):
    if kind not in ('country', 'sector', 'series') or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid catalog query')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    out = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'total': j['total'], 'records': out, 'note': NOTE}

def observations(country, indicator, sector=''):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9]{3}', country):
        raise ValueError('invalid country')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', indicator):
        raise ValueError('invalid indicator')
    if not isinstance(sector, str) or not re.fullmatch('[A-Z0-9_]{0,30}', sector):
        raise ValueError('invalid sector')
    j, u = get(f'country/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '80' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected observations')
    out = []
    for x in s['data']:
        d = {v['concept']: {'code': v['id'], 'name': v['value']} for v in x['variable']}
        if d['Country']['code'] != country or d['Series']['code'] != indicator:
            raise ValueError('unexpected dimensions')
        if not sector or d['Sector']['code'] == sector:
            out.append({'year': d['Time']['name'], 'raw_value': x['value'], 'dimensions': d})
    return {'source': u, 'last_updated': j.get('lastupdated'), 'records': out, 'note': NOTE}
