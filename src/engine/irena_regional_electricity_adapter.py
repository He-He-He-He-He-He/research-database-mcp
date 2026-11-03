"""IRENA 2026 H2 regional electricity capacity/generation PxWeb."""
import release_runtime
import requests
URL = 'https://pxweb.irena.org/api/v1/en/IRENASTAT/Power%20Capacity%20and%20Generation/Region_ELECSTAT_2026_H2_PX.px'

def electricity(region, technology='10', data_type='0', start=2020, end=2025):
    if region not in {'GLO', 'RAF', 'RAS', 'RCC', 'REA', 'RER', 'RME', 'RNA', 'ROC', 'RSA'}:
        raise ValueError('invalid IRENA region')
    if technology not in {str(i) for i in range(11)} or data_type not in {'0', '1'}:
        raise ValueError('invalid technology or data type')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 2000 <= x <= 2025) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    session = requests.Session()
    r = session.get(URL, timeout=30)
    r.raise_for_status()
    m = r.json()
    variables = {v['code']: v for v in m['variables']}
    dims = ['Region', 'Technology', 'Data Type', 'Year']
    if any((x not in variables for x in dims)):
        raise ValueError('metadata schema changed')
    yearcodes = [v for v, t in zip(variables['Year']['values'], variables['Year']['valueTexts']) if str(t).isdigit() and start <= int(t) <= end]
    if len(yearcodes) != end - start + 1:
        raise ValueError('year coverage changed')
    selected = {'Region': [region], 'Technology': [technology], 'Data Type': [data_type], 'Year': yearcodes}
    body = {'query': [{'code': x, 'selection': {'filter': 'item', 'values': selected[x]}} for x in dims], 'response': {'format': 'json-stat2'}}
    r = session.post(URL, json=body, timeout=40)
    r.raise_for_status()
    d = r.json()
    if d.get('id') != dims or d.get('size') != [1, 1, 1, len(yearcodes)]:
        raise ValueError('unexpected response dimensions')
    years = d['dimension']['Year']['category']
    values = d.get('value', [])
    statuses = d.get('status', {})

    def at(x, i):
        return x[i] if isinstance(x, list) and i < len(x) else x.get(str(i)) if isinstance(x, dict) else None
    items = [{'year': int(years['label'][key]), 'value': at(values, index), 'status': at(statuses, index)} for key, index in years['index'].items()]
    label = lambda x: d['dimension'][x]['category']['label'][selected[x][0]]
    return {'source': d.get('source'), 'region': label('Region'), 'technology': label('Technology'), 'data_type': label('Data Type'), 'items': sorted(items, key=lambda x: x['year']), 'note': 'Capacity is MW and generation GWh; 2024 generation is preliminary. Do not sum overlapping categories.'}
