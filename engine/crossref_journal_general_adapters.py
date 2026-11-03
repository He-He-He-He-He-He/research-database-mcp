"""Crossref journal discovery and journal works by ISSN."""
import release_runtime
import re
import requests

def _get(path, params):
    r = requests.get('https://api.crossref.org/' + path, params=params, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research metadata)'}, timeout=30)
    r.raise_for_status()
    data = r.json()
    message = data.get('message')
    if not isinstance(message, dict) or not isinstance(message.get('items'), list):
        raise RuntimeError('Unexpected Crossref response')
    return {'source': 'Crossref', 'total': message.get('total-results'), 'items': message['items'], 'note': 'Crossref registered metadata, not publisher full-text or library holdings.'}

def search_journals(query, size=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    _validate(size, offset)
    return _get('journals', {'query': query, 'rows': size, 'offset': offset})

def journal_works(issn, query, size=10, offset=0):
    if not isinstance(issn, str) or not re.fullmatch('\\d{4}-?\\d{3}[\\dXx]', issn):
        raise ValueError('ISSN must be eight characters with optional hyphen')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    _validate(size, offset)
    if offset + size > 10000:
        raise ValueError('Crossref works 的 offset + rows 不得超过 10000；此入口未实现 cursor 深分页')
    return _get('journals/' + issn.upper() + '/works', {'query': query, 'rows': size, 'offset': offset, 'select': 'DOI,title,author,published,URL,type,ISSN'})

def _validate(size, offset):
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be 1 to 100')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be non-negative')
