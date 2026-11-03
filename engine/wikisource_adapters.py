"""Wikisource text search and source wikitext retrieval via MediaWiki API."""
import release_runtime
import requests

def _get(language, params):
    if language not in ('zh', 'en'):
        raise ValueError('language must be zh or en')
    r = requests.get('https://' + language + '.wikisource.org/w/api.php', params=dict(params, format='json', formatversion=2), headers={'User-Agent': 'ZJUResearchToolkit/1.0 (read-only Wikisource search)'}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if 'error' in data:
        raise RuntimeError(str(data['error']))
    return data

def search(query, language='zh', size=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 50):
        raise ValueError('size must be between 1 and 50')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be a non-negative integer')
    data = _get(language, {'action': 'query', 'list': 'search', 'srsearch': query, 'srnamespace': 0, 'srlimit': size, 'sroffset': offset})
    result = data['query']
    return {'source': 'Wikisource', 'language': language, 'total': result['searchinfo']['totalhits'], 'items': result['search'], 'next_offset': data.get('continue', {}).get('sroffset'), 'note': 'Community transcriptions; verify provenance, version and individual reuse rights.'}

def page(pageid, language='zh'):
    if not isinstance(pageid, int) or isinstance(pageid, bool) or pageid < 1:
        raise ValueError('pageid must be a positive integer')
    data = _get(language, {'action': 'query', 'prop': 'revisions', 'pageids': pageid, 'rvprop': 'ids|content', 'rvslots': 'main'})
    pages = data['query']['pages']
    if len(pages) != 1 or 'missing' in pages[0]:
        raise LookupError('page not found')
    return {'source': 'Wikisource', 'language': language, 'page': pages[0], 'note': 'Content is raw wikitext and may include templates or transclusions.'}
