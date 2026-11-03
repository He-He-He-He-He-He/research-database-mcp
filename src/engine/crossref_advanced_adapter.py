"""Crossref works search with source filters, cursor and DOI metadata lookup."""
import release_runtime
import datetime, re, requests
from urllib.parse import quote
BASE = 'https://api.crossref.org/works'

def _fetch(url, params=None):
    with requests.get(url, params=params, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        source = r.url
        body = bytearray()
        for part in r.iter_content(65536):
            body.extend(part)
            if len(body) > 10000000:
                raise ValueError('Crossref response exceeds 10 MB')
    import json
    try:
        j = json.loads(body)
    except ValueError:
        raise RuntimeError('Crossref returned non-JSON') from None
    if not isinstance(j, dict) or j.get('status') != 'ok' or (not isinstance(j.get('message'), dict)):
        raise RuntimeError('unexpected Crossref response')
    return (source, j['message'])

def _date(v):
    if not isinstance(v, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', v):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        datetime.date.fromisoformat(v)
    except ValueError:
        raise ValueError('invalid date') from None
    return v

def search(query, start=None, end=None, work_type='', issn='', rows=10, cursor='*'):
    if not isinstance(query, str) or not query.strip() or len(query) > 500 or any((ord(c) < 32 for c in query)):
        raise ValueError('invalid query')
    if (start is None) != (end is None):
        raise ValueError('provide both dates')
    filters = []
    if start is not None:
        start = _date(start)
        end = _date(end)
        if start > end:
            raise ValueError('date range reversed')
        filters.extend(['from-pub-date:' + start, 'until-pub-date:' + end])
    if not isinstance(work_type, str) or (work_type and (not re.fullmatch('[a-z0-9-]{1,50}', work_type))):
        raise ValueError('invalid work type')
    if not isinstance(issn, str) or (issn and (not re.fullmatch('\\d{4}-\\d{3}[\\dXx]', issn))):
        raise ValueError('invalid ISSN')
    if work_type:
        filters.append('type:' + work_type)
    if issn:
        filters.append('issn:' + issn.upper())
    if type(rows) is not int or not 1 <= rows <= 50 or (not isinstance(cursor, str)) or (not cursor) or (len(cursor) > 2000) or any((ord(c) < 32 for c in cursor)):
        raise ValueError('invalid rows or cursor')
    p = {'query.bibliographic': query, 'rows': rows, 'cursor': cursor}
    if filters:
        p['filter'] = ','.join(filters)
    source, j = _fetch(BASE, p)
    items = j.get('items')
    total = j.get('total-results')
    if not isinstance(items, list) or type(total) is not int or len(items) > rows or any((not isinstance(x, dict) or not isinstance(x.get('DOI'), str) for x in items)):
        raise RuntimeError('unexpected Crossref search response')
    return {'source_url': source, 'query': query, 'filters': filters, 'total_results': total, 'returned': len(items), 'next_cursor_candidate': j.get('next-cursor') if items else None, 'items': items, 'note': 'Crossref 搜索和公布日期筛选遵循来源元数据，出版日期字段可能存在在线/印刷等差异；DOI题录不代表全文或授权。游标和相关度排序不保证跨请求快照一致，候选游标不保证还有结果。'}

def detail(doi):
    if not isinstance(doi, str) or not re.fullmatch('10\\.\\d{4,9}/[^\\s\\x00-\\x1f]{1,450}', doi, re.I):
        raise ValueError('invalid DOI')
    source, j = _fetch(BASE + '/' + quote(doi, safe=''))
    if str(j.get('DOI', '')).casefold() != doi.casefold():
        raise RuntimeError('Crossref returned a different DOI')
    return {'source_url': source, 'record': j, 'note': 'Crossref 提供出版商注册的元数据，不证明全文可读；不同出版日期、撤稿/更正关联及许可需核原记录。'}
