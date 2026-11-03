"""UNDP Transparency Portal public project directory and filtered annual listings."""
import release_runtime
import json
import re
import requests
BASE = 'https://api.open.undp.org/api/v1/'

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        body = r.raw.read(3000001, decode_content=True)
    if len(body) > 3000000:
        raise ValueError('response exceeds size limit')
    return json.loads(body)

def countries():
    data = _get('master/country', {'donor': ''})
    if data.get('status') != 200 or not isinstance(data.get('data'), list):
        raise ValueError('unexpected country response')
    return [{k: x.get(k) for k in ('name', 'iso2', 'iso3', 'unit_type', 'is_donor', 'is_recipient')} for x in data['data']]

def years():
    data = _get('master/project_time_line')
    if not isinstance(data, list) or any((type(x) is not int for x in data)):
        raise ValueError('unexpected year response')
    return data

def query(country_code, year, *, keyword='', offset=0, limit=20):
    if not re.fullmatch('[A-Z]{3}', country_code) or type(year) is not int or (not 2012 <= year <= 2100):
        raise ValueError('country must be ISO3 and year >= 2012')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(offset) is not int or (offset < 0) or (type(limit) is not int) or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or pagination')
    p = {'year': year, 'limit': limit, 'offset': offset, 'operating_units': country_code, 'keyword': keyword, 'budget_sources': '', 'sectors': '', 'budget_type': '', 'sdgs': '', 'signature_solution': '', 'marker_type': '', 'marker_id': '', 'mco': ''}
    response = _get('project/list/', p)
    data = response.get('data')
    if response.get('status') != 200 or not isinstance(data, dict) or (not isinstance(data.get('data'), list)):
        raise ValueError('unexpected project response')
    return {'source': 'UNDP Transparency Portal', 'source_url': 'https://open.undp.org/', 'country_code': country_code, 'year_filter': year, 'offset': offset, 'count': data.get('count'), 'records': data['data'], 'note': 'Budget and expense are source fields; currency, price basis and period require source verification. Project listing does not imply completion. Records may overlap IATI; do not sum without reconciliation. Redistribution rights are not verified.'}
