"""African Development Bank MapAfrica public frontend data endpoints."""
import release_runtime
import re
import requests
BASE = 'https://mapafrica.afdb.org/api/v15/'
PAGE = 'https://mapafrica.afdb.org/'

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=45)
    r.raise_for_status()
    return r.json()

def projects(country='', page=1, limit=20):
    if country and (not re.fullmatch('[A-Za-z]{2}', country)):
        raise ValueError('country must be a two-letter country code')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('invalid page')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    params = {'lang': 'en', 'currency': 'UA', 'page': page, 'per_page': limit}
    if country:
        params['country'] = country.upper()
    result = _get('activities', params)
    if not isinstance(result, dict) or not isinstance(result.get('results'), list):
        raise ValueError('unexpected response')
    return {'source': BASE + 'activities', 'homepage': PAGE, 'request': params, 'unit': 'UA (AfDB unit of account)', 'notes': ['Commitments, disbursements, budget and expenditure are distinct source fields and should not be added; scope and completeness require project-level verification.', 'Country filter is for nationally coded projects; multinational projects can be omitted. Status and sector codes require official codelists.', 'API is used by the official MapAfrica frontend but is not documented here as a stable public developer interface. Total counts are not returned by this endpoint; a full page does not guarantee another page.'], 'data': result}

def details(identifier):
    if not re.fullmatch('[A-Za-z0-9-]{1,100}', identifier):
        raise ValueError('invalid IATI identifier')
    return {'source': BASE + 'activities/' + identifier, 'unit': 'UA (AfDB unit of account)', 'note': 'Official project data; inspect field definitions, status and dates before comparison.', 'data': _get('activities/' + identifier, {'lang': 'en', 'currency': 'UA'})}

def codelists():
    return {'source': BASE + 'codelists', 'data': _get('codelists', {'lang': 'en'})}
