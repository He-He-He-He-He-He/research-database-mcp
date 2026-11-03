"""Wikimedia Analytics edits-per-page timeseries."""
import release_runtime
import re
from datetime import datetime
from urllib.parse import quote
import requests

def edits(title, start, end, language='en', editor_type='user', granularity='daily'):
    if not isinstance(title, str) or not title.strip():
        raise ValueError('title must be non-empty')
    if not isinstance(language, str) or not re.fullmatch('[a-z][a-z0-9-]{0,19}', language):
        raise ValueError('invalid language')
    if editor_type not in ('user', 'all-editor-types'):
        raise ValueError('editor_type must be user or all-editor-types')
    if granularity not in ('daily', 'monthly'):
        raise ValueError('granularity must be daily or monthly')
    try:
        a, b = (datetime.strptime(x, '%Y%m%d') for x in (start, end))
        if a.strftime('%Y%m%d') != start or b.strftime('%Y%m%d') != end or b < a:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('dates must be YYYYMMDD and ordered') from None
    parts = [language + '.wikipedia.org', quote(title.strip().replace(' ', '_'), safe=''), editor_type, granularity, start, end]
    r = requests.get('https://wikimedia.org/api/rest_v1/metrics/edits/per-page/' + '/'.join(parts), headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research analytics)'}, timeout=30)
    r.raise_for_status()
    groups = r.json().get('items')
    if not isinstance(groups, list) or len(groups) != 1 or (not isinstance(groups[0].get('results'), list)):
        raise RuntimeError('Unexpected Wikimedia edits response')
    return {'source': 'Wikimedia Analytics', 'data': groups[0], 'note': 'Counts edits, not distinct editors. Dates with no returned data are omitted; a 404 is not automatically proof of zero.'}
