"""IAEA PRIS Analytics public summary statistics currently displayed by the site."""
import release_runtime
import re
import requests
BASE = 'https://pris-stats.iaea.org'

def _fetch(path):
    url = BASE + path
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    if len(response.content) > 2000000:
        raise ValueError('Unexpected response size')
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise ValueError('Unexpected PRIS response')
    return (url, payload['items'])

def world():
    url, items = _fetch('/worldstatistics/world-statistics/')
    return {'source_url': url, 'source': 'IAEA PRIS Analytics', 'items': items, 'note': 'Current site summary; operating and suspended operation are separate. Energy item refers to the year in its title; status snapshots have no observed timestamp.'}

def country(country_code):
    if not isinstance(country_code, str) or not re.fullmatch('[A-Za-z]{2}', country_code):
        raise ValueError('country_code must be two letters')
    code = country_code.upper()
    url, items = _fetch('/countrystatistics/country-statistics/')
    rows = [x for x in items if str(x.get('countryCode', '')).upper() == code]
    return {'source_url': url, 'source': 'IAEA PRIS Analytics', 'country_code': code, 'items': rows, 'note': 'Site summary raw fields; absent row is not evidence of zero. NuclearShare uses a different metric/unit from reactor counts and capacities.'}
