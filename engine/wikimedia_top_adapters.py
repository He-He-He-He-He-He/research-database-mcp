"""Wikimedia Analytics top-viewed Wikipedia pages by day or month."""
import release_runtime
import re
from datetime import date
import requests

def top(year, month, day=None, language='en', access='all-access', limit=20):
    if not all((isinstance(x, int) and (not isinstance(x, bool)) for x in (year, month))):
        raise ValueError('year and month must be integers')
    if day is not None and (not isinstance(day, int) or isinstance(day, bool)):
        raise ValueError('day must be an integer or None')
    try:
        date(year, month, day if day is not None else 1)
    except ValueError:
        raise ValueError('invalid date') from None
    if not isinstance(language, str) or not re.fullmatch('[a-z][a-z0-9-]{0,19}', language):
        raise ValueError('invalid language code')
    if access not in ('all-access', 'desktop', 'mobile-app', 'mobile-web'):
        raise ValueError('invalid access')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 1000):
        raise ValueError('limit must be from 1 to 1000')
    day_part = 'all-days' if day is None else f'{day:02d}'
    url = f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{language}.wikipedia.org/{access}/{year:04d}/{month:02d}/{day_part}'
    r = requests.get(url, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research analytics)'}, timeout=30)
    r.raise_for_status()
    groups = r.json().get('items')
    if not isinstance(groups, list) or len(groups) != 1 or (not isinstance(groups[0].get('articles'), list)):
        raise RuntimeError('Unexpected Wikimedia response')
    group = groups[0]
    return {'source': 'Wikimedia Analytics', 'project': group['project'], 'access': group['access'], 'year': year, 'month': month, 'day': day, 'items': group['articles'][:limit], 'note': 'Most-viewed pages, not unique visitors; includes non-article entries when present. Rankings limited to API top 1000.'}
