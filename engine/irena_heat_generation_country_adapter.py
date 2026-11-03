"""IRENASTAT 2026 H2 heat generation country PxWeb table."""
import release_runtime
import re
import requests
URL = 'https://pxweb.irena.org/api/v1/en/IRENASTAT/Heat%20Generation/HEATGEN_2026_H2_PX.px'

def heat(country, technology='4', connection='0', start=2022, end=2024):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be an uppercase IRENA alpha-3 code')
    if not isinstance(technology, str) or not isinstance(connection, str):
        raise ValueError('technology and connection must be codes as strings')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 2000 <= x <= 2024) for x in (start, end))) or start > end:
        raise ValueError('years must be in 2000–2024, in order')
    s = requests.Session()
    r = s.get(URL, timeout=30)
    r.raise_for_status()
    m = r.json()
    dims = ['Country/area', 'Technology', 'Grid connection', 'Year']
    v = {x['code']: x for x in m['variables']}
    if any((x not in v for x in dims)):
        raise ValueError('Unexpected metadata dimensions')
    for dim, val in [('Country/area', country), ('Technology', technology), ('Grid connection', connection)]:
        if val not in v[dim]['values']:
            raise ValueError('Unknown ' + dim + ' code')
    years = [c for c, n in zip(v['Year']['values'], v['Year']['valueTexts']) if n.isdigit() and start <= int(n) <= end]
    if len(years) != end - start + 1:
        raise ValueError('Missing year in source')
    chosen = {'Country/area': [country], 'Technology': [technology], 'Grid connection': [connection], 'Year': years}
    body = {'query': [{'code': d, 'selection': {'filter': 'item', 'values': chosen[d]}} for d in dims], 'response': {'format': 'json-stat2'}}
    r = s.post(URL, json=body, timeout=40)
    r.raise_for_status()
    d = r.json()
    if d.get('id') != dims or d.get('size') != [1, 1, 1, len(years)]:
        raise ValueError('Unexpected response dimensions')
    cat = d['dimension']['Year']['category']
    values = d.get('value', [])
    status = d.get('status', {})

    def at(x, i):
        return x[i] if isinstance(x, list) and i < len(x) else x.get(str(i)) if isinstance(x, dict) else None
    items = [{'year': int(cat['label'][k]), 'value': at(values, i), 'status': at(status, i)} for k, i in cat['index'].items()]
    label = lambda dim: d['dimension'][dim]['category']['label'][chosen[dim][0]]
    return {'source_url': URL, 'source': d.get('source'), 'country': label('Country/area'), 'technology': label('Technology'), 'grid_connection': label('Grid connection'), 'unit': 'terajoules (TJ)', 'items': sorted(items, key=lambda x: x['year']), 'note': 'Heat production, not electricity output. Commercial heat and CHP are separate categories; missing is not zero. Coverage restricted to countries in source.'}
