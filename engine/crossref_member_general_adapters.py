"""Crossref member discovery and works registered by a selected member."""
import release_runtime
import requests

def _get(path, params):
    r = requests.get('https://api.crossref.org/' + path, params=params, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research metadata)'}, timeout=30)
    r.raise_for_status()
    data = r.json().get('message')
    if not isinstance(data, dict) or not isinstance(data.get('items'), list):
        raise RuntimeError('Unexpected Crossref response')
    return {'source': 'Crossref', 'total': data.get('total-results'), 'items': data['items'], 'note': 'Members are metadata depositors; results do not establish library holdings or access.'}

def search_members(query, size=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    _validate(size, offset)
    return _get('members', {'query': query, 'rows': size, 'offset': offset})

def member_works(member_id, query, size=10, offset=0):
    if not str(member_id).isdigit() or isinstance(member_id, bool):
        raise ValueError('member_id must be numeric')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    _validate(size, offset)
    if offset + size > 10000:
        raise ValueError('Crossref works 的 offset + rows 不得超过 10000；此入口未实现 cursor 深分页')
    return _get('members/' + str(member_id) + '/works', {'query': query, 'rows': size, 'offset': offset, 'select': 'DOI,title,author,published,URL,type,publisher'})

def _validate(size, offset):
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be 1 to 100')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be non-negative')
