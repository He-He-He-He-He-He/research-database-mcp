"""Wikimedia per-article historical pageview time series."""
import release_runtime
from datetime import datetime
from urllib.parse import quote
import re
import requests

def pageviews(title, start, end, language='en', access='all-access', agent='user', granularity='daily'):
    if not isinstance(title, str) or not title.strip():
        raise ValueError('title must be non-empty')
    if not isinstance(language, str) or not re.fullmatch('[a-z][a-z0-9-]{0,19}', language):
        raise ValueError('invalid Wikipedia language code')
    if access not in ('all-access', 'desktop', 'mobile-app', 'mobile-web'):
        raise ValueError('invalid access')
    if agent not in ('user', 'all-agents', 'spider', 'automated'):
        raise ValueError('invalid agent')
    if granularity not in ('daily', 'monthly'):
        raise ValueError('granularity must be daily or monthly')
    try:
        a, b = (datetime.strptime(x, '%Y%m%d') for x in (start, end))
        if a.strftime('%Y%m%d') != start or b.strftime('%Y%m%d') != end or b < a:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('start/end must be valid YYYYMMDD with start <= end') from None
    path = '/'.join([language + '.wikipedia.org', access, agent, quote(title.strip().replace(' ', '_'), safe=''), granularity, start, end])
    r = requests.get('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/' + path, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research analytics)'}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('items'), list):
        raise RuntimeError('Unexpected Wikimedia Analytics response')
    return {'source': 'Wikimedia Analytics API', 'items': data['items'], 'note': 'Page views are requests, not unique people; redirects and bot classification have specific rules. Missing dates are not automatically zero.'}
