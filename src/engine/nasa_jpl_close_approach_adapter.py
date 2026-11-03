"""NASA JPL SBDB close-approach data for a numbered small body to Earth."""
import release_runtime
import datetime, re
import requests
URL = 'https://ssd-api.jpl.nasa.gov/cad.api'
DOC = 'https://ssd-api.jpl.nasa.gov/doc/cad.html'

def _date(s):
    if not isinstance(s, str) or not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', s):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        raise ValueError('invalid date') from None

def approaches(designation, start, end, distance_au=0.2, limit=10, offset=0):
    if not isinstance(designation, str) or not re.fullmatch('[0-9]{1,7}', designation) or int(designation) == 0:
        raise ValueError('designation must be a positive numbered small-body identifier')
    a, b = (_date(start), _date(end))
    if a > b or (b - a).days > 73050:
        raise ValueError('date interval must be ordered and at most 200 years')
    if isinstance(distance_au, bool) or not isinstance(distance_au, (int, float)) or (not 0 < distance_au <= 1):
        raise ValueError('distance_au must be positive and <= 1')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset out of range')
    p = {'des': designation, 'date-min': start, 'date-max': end, 'dist-max': str(distance_au), 'body': 'Earth', 'sort': 'date', 'limit': limit}
    if offset:
        p['limit-from'] = offset
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('Unexpected source size')
    d = r.json()
    if not isinstance(d, dict) or d.get('signature', {}).get('version') != '1.5' or (not isinstance(d.get('count'), int)):
        raise ValueError('Unexpected JPL response version or format')
    fields = d.get('fields', [])
    rows = d.get('data', [])
    if not isinstance(fields, list) or not isinstance(rows, list) or any((not isinstance(x, list) or len(x) != len(fields) for x in rows)):
        raise ValueError('Unexpected JPL table shape')
    return {'source_url': r.url, 'documentation': DOC, 'signature': d['signature'], 'total': d.get('total'), 'count': d['count'], 'items': [dict(zip(fields, x)) for x in rows], 'note': 'Earth close approaches, not impact predictions. cd is TDB, distances in AU (nominal and 3-sigma bounds), velocity km/s; predictions can change with orbital solutions.'}
