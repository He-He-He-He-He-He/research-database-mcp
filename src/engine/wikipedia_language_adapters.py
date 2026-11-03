"""Get corresponding Wikipedia pages across languages via MediaWiki API."""
import release_runtime
import re
import requests

def links(title, language='en', target=None):
    if not isinstance(title, str) or not title.strip() or '|' in title:
        raise ValueError('title must be a single non-empty page title')
    for code in (language, target):
        if code is not None and (not isinstance(code, str) or not re.fullmatch('[a-z][a-z0-9-]{0,19}', code)):
            raise ValueError('invalid language code')
    params = {'action': 'query', 'prop': 'langlinks', 'titles': title, 'redirects': 1, 'llprop': 'url|langname', 'lllimit': 500, 'format': 'json', 'formatversion': 2}
    if target:
        params['lllang'] = target
    r = requests.get('https://' + language + '.wikipedia.org/w/api.php', params=params, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research reference lookup)'}, timeout=30)
    r.raise_for_status()
    d = r.json()
    if 'error' in d:
        raise RuntimeError(str(d['error']))
    pages = d['query']['pages']
    if len(pages) != 1 or 'missing' in pages[0]:
        raise LookupError('Wikipedia page not found')
    return {'source': 'Wikipedia', 'language': language, 'page': pages[0]['title'], 'items': pages[0].get('langlinks', []), 'continuation': d.get('continue'), 'note': 'Linked pages concern a shared topic but need not be translations or equivalent coverage.'}
