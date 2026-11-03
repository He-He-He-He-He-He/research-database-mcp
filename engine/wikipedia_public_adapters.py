"""Wikipedia public search and article introduction via MediaWiki API."""
import release_runtime
import re
import requests

def _get(language, params):
    if not isinstance(language, str) or not re.fullmatch('[a-z][a-z0-9-]{0,19}', language):
        raise ValueError('invalid Wikipedia language code')
    r = requests.get('https://' + language + '.wikipedia.org/w/api.php', params=dict(params, format='json', formatversion=2), headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research reference lookup)'}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if 'error' in data:
        raise RuntimeError(str(data['error']))
    return data

def search(query, language='en', size=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 50):
        raise ValueError('size must be 1 to 50')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be non-negative')
    d = _get(language, {'action': 'query', 'list': 'search', 'srsearch': query, 'srnamespace': 0, 'srlimit': size, 'sroffset': offset})
    return {'source': 'Wikipedia', 'language': language, 'total': d['query']['searchinfo']['totalhits'], 'items': d['query']['search'], 'next_offset': d.get('continue', {}).get('sroffset'), 'note': 'Community-edited reference; verify claims against cited primary sources.'}

def introduction(pageid, language='en'):
    if not isinstance(pageid, int) or isinstance(pageid, bool) or pageid < 1:
        raise ValueError('pageid must be positive')
    d = _get(language, {'action': 'query', 'prop': 'extracts|info', 'inprop': 'url', 'pageids': pageid, 'exintro': 1, 'explaintext': 1})
    pages = d['query']['pages']
    if len(pages) != 1 or 'missing' in pages[0]:
        raise LookupError('page not found')
    return {'source': 'Wikipedia', 'language': language, 'page': pages[0], 'note': 'Introduction only, not full article; check page history, sources and reuse license.'}
