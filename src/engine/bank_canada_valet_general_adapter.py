"""Bank of Canada's general public Valet series discovery and observations."""
import release_runtime
import datetime
import re
import requests
BASE = 'https://www.bankofcanada.ca/valet/'
NOTES = ['Series definitions, unit, currency direction and frequency are source-specific; a daily average exchange rate is not a transaction quote.', 'Current values may be revised; dates of observations do not establish the date at which the values were published or available.', 'Empty dates and missing observations are not zero. Respect the Bank of Canada terms, avoid high-frequency requests and cache where appropriate.']

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('Unexpected Bank of Canada response')
    return j

def catalog(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid catalogue query')
    j = _get('lists/series/json')
    s = j.get('series')
    if not isinstance(s, dict):
        raise ValueError('Unexpected Bank of Canada catalogue')
    k = keyword.casefold()
    rows = [{'code': code, **info} for code, info in s.items() if isinstance(info, dict) and k in (code + ' ' + str(info.get('label', '')) + ' ' + str(info.get('description', ''))).casefold()]
    return {'source': BASE + 'lists/series/json', 'terms': j.get('terms'), 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}

def observations(code, start, end):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', code):
        raise ValueError('Invalid series code')
    for d in (start, end):
        if not isinstance(d, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', d):
            raise ValueError('Dates must be YYYY-MM-DD')
        datetime.date.fromisoformat(d)
    if start > end:
        raise ValueError('Start after end')
    p = {'start_date': start, 'end_date': end}
    j = _get('observations/' + code + '/json', p)
    detail = j.get('seriesDetail')
    rows = j.get('observations')
    if not isinstance(detail, dict) or code not in detail or (not isinstance(rows, list)):
        raise ValueError('Unexpected Bank of Canada series response')
    if any((not isinstance(r, dict) or not start <= r.get('d', '') <= end for r in rows)):
        raise ValueError('Observation outside requested dates')
    return {'source': BASE + 'observations/' + code + '/json', 'request': p, 'terms': j.get('terms'), 'series_detail': detail, 'notes': NOTES, 'observations': rows}
