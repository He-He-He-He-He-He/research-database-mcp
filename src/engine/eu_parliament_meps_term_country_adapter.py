"""European Parliament members filtered by parliamentary term and country."""
import release_runtime
import requests
BASE = 'https://data.europarl.europa.eu/api/v2/meps'
DOC = 'https://data.europarl.europa.eu/en/developer-corner/opendata-api'
COUNTRIES = {'BE', 'BG', 'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'UK'}

def members_by_term_country(term, country, limit=10, offset=0):
    if isinstance(term, bool) or not isinstance(term, int) or (not 0 <= term <= 10):
        raise ValueError('term must be 0–10')
    if not isinstance(country, str) or country not in COUNTRIES:
        raise ValueError('country must be supported uppercase country code')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 9950):
        raise ValueError('offset must be 0–9950')
    r = requests.get(BASE, params={'format': 'application/ld+json', 'parliamentary-term': term, 'country-of-representation': country, 'limit': limit, 'offset': offset}, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('data'), list):
        raise ValueError('Unexpected response shape')
    return {'source_url': r.url, 'documentation': DOC, 'term': term, 'country': country, 'items': d['data'], 'note': 'Members during the term, not necessarily members today; confirm individual membership dates. Source has no reported total in this response; cross-page consistency is not guaranteed.'}
