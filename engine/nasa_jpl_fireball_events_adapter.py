"""NASA JPL reported fireball events, bounded by observed date."""
import release_runtime
import datetime, re
import requests
URL = 'https://ssd-api.jpl.nasa.gov/fireball.api'
DOC = 'https://ssd-api.jpl.nasa.gov/doc/fireball.html'

def _date(s):
    if not isinstance(s, str) or not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', s):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        raise ValueError('invalid date') from None

def events(start, end, limit=10):
    a, b = (_date(start), _date(end))
    if a > b or (b - a).days > 366:
        raise ValueError('Date range must be ordered and at most 366 days')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    params = {'date-min': start, 'date-max': end + 'T23:59:59', 'limit': limit, 'sort': '-date'}
    r = requests.get(URL, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('Unexpected source size')
    d = r.json()
    if not isinstance(d, dict) or d.get('signature', {}).get('version') != '1.2':
        raise ValueError('Unexpected JPL API version')
    fields = d.get('fields', [])
    rows = d.get('data', [])
    if not isinstance(fields, list) or not isinstance(rows, list) or any((not isinstance(x, list) or len(x) != len(fields) for x in rows)):
        raise ValueError('Unexpected JPL table structure')
    return {'source_url': r.url, 'documentation': DOC, 'signature': d['signature'], 'items': [dict(zip(fields, x)) for x in rows], 'returned_count': len(rows), 'possibly_truncated': len(rows) == limit, 'note': 'Observed sensor-reported peak-brightness events; not complete coverage. energy = 10^10 J radiated, impact-e = kilotons estimated; null fields are not zero.'}
