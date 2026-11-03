"""NASA EONET curated natural-event metadata by interval and category."""
import release_runtime
import re
from datetime import date
import requests

def events(start, end, category=None, status='all', limit=50):
    try:
        a, b = (date.fromisoformat(start), date.fromisoformat(end))
        if a.isoformat() != start or b.isoformat() != end or b < a:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('start and end must be ordered YYYY-MM-DD dates') from None
    if category is not None and (not isinstance(category, str) or not re.fullmatch('[A-Za-z]+', category)):
        raise ValueError('category must be an EONET category ID')
    if status not in ('all', 'open', 'closed'):
        raise ValueError('status must be all, open, or closed')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 1000):
        raise ValueError('limit must be 1 to 1000')
    params = {'start': start, 'end': end, 'status': status, 'limit': limit}
    if category:
        params['category'] = category
    r = requests.get('https://eonet.gsfc.nasa.gov/api/v3/events', params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('events'), list):
        raise RuntimeError('Unexpected NASA EONET response')
    return {'source': 'NASA EONET', 'start': start, 'end': end, 'category': category, 'status': status, 'limit': limit, 'items': data['events'], 'note': 'Curated event metadata is not an exhaustive disaster census; geometry and dates can be approximate. Results may be truncated by limit.'}
