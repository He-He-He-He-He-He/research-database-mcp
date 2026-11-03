"""Estimated unique devices accessing a Wikipedia language project."""
import release_runtime
import re
from datetime import datetime
import requests

def devices(start, end, language='en', access='all-sites', granularity='monthly'):
    if not isinstance(language, str) or not re.fullmatch('[a-z][a-z0-9-]{0,19}', language):
        raise ValueError('invalid language')
    if access not in ('all-sites', 'desktop-site', 'mobile-site'):
        raise ValueError('invalid access site')
    if granularity not in ('daily', 'monthly'):
        raise ValueError('granularity must be daily or monthly')
    try:
        a, b = (datetime.strptime(x, '%Y%m%d') for x in (start, end))
        if a.strftime('%Y%m%d') != start or b.strftime('%Y%m%d') != end or b < a:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError('dates must be YYYYMMDD and ordered') from None
    path = f'{language}.wikipedia.org/{access}/{granularity}/{start}/{end}'
    r = requests.get('https://wikimedia.org/api/rest_v1/metrics/unique-devices/' + path, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research analytics)'}, timeout=30)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('items'), list):
        raise RuntimeError('Unexpected Wikimedia response')
    return {'source': 'Wikimedia Analytics', 'items': d['items'], 'note': 'Estimated unique browser devices for the entire project, not people or one article; estimates use cookies and include an offset. Do not sum daily values to estimate monthly reach.'}
