"""DataCite resource types and bounded filtered DOI discovery."""
import release_runtime
import re, requests
from urllib.parse import urlsplit, parse_qs
BASE = 'https://api.datacite.org'

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        url = r.url
        raw = bytearray()
        for b in r.iter_content(65536):
            raw.extend(b)
            if len(raw) > 10000000:
                raise ValueError('DataCite response exceeds 10 MB')
    import json
    try:
        j = json.loads(raw)
    except ValueError:
        raise RuntimeError('DataCite returned non-JSON') from None
    if not isinstance(j, dict) or not isinstance(j.get('data'), list):
        raise RuntimeError('unexpected DataCite response')
    return (url, j)

def types(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    u, j = _get('/resource-types')
    rows = j['data']
    if any((not isinstance(x, dict) or x.get('type') != 'resource-types' for x in rows)):
        raise RuntimeError('unexpected resource type data')
    found = [x for x in rows if keyword.casefold() in (str(x.get('id', '')) + ' ' + str((x.get('attributes') or {}).get('title', ''))).casefold()]
    return {'source_url': u, 'count': len(found), 'types': found, 'note': '官方资源类型目录；类型与内容可用性、许可不同。'}

def search(query, resource_type='', published=None, client_id='', size=10, cursor='1'):
    if not isinstance(query, str) or not query.strip() or len(query) > 300 or any((ord(c) < 32 for c in query)):
        raise ValueError('invalid query')
    if not isinstance(resource_type, str) or (resource_type and (not re.fullmatch('[a-z0-9-]{1,50}', resource_type))):
        raise ValueError('invalid resource type')
    if published is not None and (type(published) is not int or not 1900 <= published <= 2100):
        raise ValueError('invalid published year')
    if not isinstance(client_id, str) or (client_id and (not re.fullmatch('[a-zA-Z0-9._-]{1,100}', client_id))):
        raise ValueError('invalid repository client ID')
    if type(size) is not int or not 1 <= size <= 50 or (not isinstance(cursor, str)) or (not cursor) or (len(cursor) > 2000) or any((ord(c) < 32 for c in cursor)):
        raise ValueError('invalid page size or cursor')
    p = {'query': query, 'page[size]': size, 'page[cursor]': cursor}
    if resource_type:
        p['resource-type-id'] = resource_type
    if published is not None:
        p['published'] = str(published)
    if client_id:
        p['client-id'] = client_id
    u, j = _get('/dois', p)
    rows = j['data']
    total = (j.get('meta') or {}).get('total')
    if type(total) is not int or len(rows) > size or any((not isinstance(x, dict) or x.get('type') != 'dois' or (not isinstance(x.get('id'), str)) for x in rows)):
        raise RuntimeError('unexpected DataCite DOI results')
    next_url = (j.get('links') or {}).get('next')
    next_cursor = None
    if next_url:
        z = urlsplit(next_url)
        if z.scheme != 'https' or z.netloc != 'api.datacite.org' or z.path != '/dois':
            raise RuntimeError('unexpected DataCite continuation URL')
        values = parse_qs(z.query).get('page[cursor]', [])
        if len(values) != 1:
            raise RuntimeError('invalid continuation cursor')
        next_cursor = values[0]
    return {'source_url': u, 'query': query, 'resource_type': resource_type or None, 'published_filter': published, 'client_id': client_id or None, 'total': total, 'next_cursor_candidate': next_cursor, 'items': rows, 'note': 'published 是 DataCite 来源日期筛选，须核记录 publicationYear 与实际发布日期；搜索与游标跨请求可能变化。DOI 元数据不等于文件可用、全文或授权；具体访问及许可核原记录。'}
