"""IRENA public finance commitments by recipient and technology."""
import release_runtime
import re
import requests
URL = 'https://pxweb.irena.org/api/v1/en/IRENASTAT/Finance/PUBFIN_2026_H2_PX.px'

def commitments(country, technology='1', start=2020, end=2024):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be IRENA alpha-3 code')
    if technology not in {str(i) for i in range(20)}:
        raise ValueError('invalid technology code')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 2000 <= x <= 2024) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    s = requests.Session()
    r = s.get(URL, timeout=30)
    r.raise_for_status()
    m = r.json()
    dims = ['Country/area', 'Technology', 'Year']
    v = {x['code']: x for x in m['variables']}
    if any((x not in v for x in dims)) or country not in v['Country/area']['values'] or technology not in v['Technology']['values']:
        raise ValueError('invalid code or changed metadata')
    years = [c for c, n in zip(v['Year']['values'], v['Year']['valueTexts']) if n.isdigit() and start <= int(n) <= end]
    if len(years) != end - start + 1:
        raise ValueError('missing years')
    choices = {'Country/area': [country], 'Technology': [technology], 'Year': years}
    body = {'query': [{'code': d, 'selection': {'filter': 'item', 'values': choices[d]}} for d in dims], 'response': {'format': 'json-stat2'}}
    r = s.post(URL, json=body, timeout=40)
    r.raise_for_status()
    data = r.json()
    if data.get('id') != dims or data.get('size') != [1, 1, len(years)]:
        raise ValueError('unexpected dimensions')
    cat = data['dimension']['Year']['category']
    vals = data.get('value', [])
    status = data.get('status', {})

    def at(x, i):
        return x[i] if isinstance(x, list) and i < len(x) else x.get(str(i)) if isinstance(x, dict) else None
    items = [{'year': int(cat['label'][k]), 'value': at(vals, i), 'status': at(status, i)} for k, i in cat['index'].items()]
    label = lambda d: data['dimension'][d]['category']['label'][choices[d][0]]
    return {'source': data.get('source'), 'country': label('Country/area'), 'technology': label('Technology'), 'unit': 'million USD at 2023 prices and exchange rates', 'items': sorted(items, key=lambda x: x['year']), 'note': 'Recipient-country commitments, not necessarily disbursed or actual investment; categories may overlap.'}
