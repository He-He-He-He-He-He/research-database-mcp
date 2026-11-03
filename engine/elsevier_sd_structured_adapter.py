"""ScienceDirect v2 native structured search using local Elsevier credentials."""
import release_runtime
import re, requests
from elsevier_sciencedirect_search_adapter import _key, URL, DOC

def search(query='', title='', authors='', publication='', start_year=None, end_year=None, open_access=False, offset=0, limit=5):
    for v in (query, title, authors, publication):
        if not isinstance(v, str) or len(v) > 250 or re.search('[\\x00-\\x1f]', v):
            raise ValueError('text fields must be printable, at most 250 characters')
    if not any((x.strip() for x in (query, title, authors, publication))):
        raise ValueError('provide at least one search field')
    if (start_year is None) != (end_year is None) or (start_year is not None and (type(start_year) is not int or type(end_year) is not int or (not 1900 <= start_year <= end_year <= 2100))):
        raise ValueError('provide valid start and end years')
    if type(open_access) is not bool or type(offset) is not int or (not 0 <= offset <= 5990) or (type(limit) is not int) or (not 1 <= limit <= 10):
        raise ValueError('invalid open access or page selection')
    body = {'display': {'offset': offset, 'show': 10}}
    for key, value in [('qs', query), ('title', title), ('authors', authors), ('pub', publication)]:
        if value.strip():
            body[key] = value.strip()
    if start_year is not None:
        body['date'] = str(start_year) + '-' + str(end_year)
    if open_access:
        body['filters'] = {'openAccess': True}
    try:
        r = requests.put(URL, json=body, headers={'X-ELS-APIKey': _key(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('ScienceDirect network request failed: ' + type(e).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('ScienceDirect returned HTTP ' + str(r.status_code))
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('ScienceDirect returned non-JSON') from None
    rows = j.get('results', []) if isinstance(j, dict) else None
    total = j.get('resultsFound') if isinstance(j, dict) else None
    if not isinstance(rows, list) or type(total) is not int or total < 0 or (len(rows) > 10) or any((not isinstance(x, dict) or not isinstance(x.get('title'), str) or (not isinstance(x.get('pii'), str)) for x in rows)):
        raise RuntimeError('unexpected ScienceDirect search response')
    if total == 0 and rows:
        raise RuntimeError('source returned rows for zero total')
    if open_access and any((x.get('openAccess') is not True for x in rows)):
        raise RuntimeError('source response does not match open-access filter')
    if start_year is not None:
        for x in rows:
            date = x.get('publicationDate')
            if isinstance(date, str) and re.match('^\\d{4}', date) and (not start_year <= int(date[:4]) <= end_year):
                raise RuntimeError('publication date outside requested years')
    selected = rows[:limit]
    next_offset = offset + len(selected) if selected and offset + len(selected) < total and (offset + len(selected) <= 5990) else None
    return {'source': URL, 'documentation': DOC, 'request': body, 'total_raw': total, 'upstream_received': len(rows), 'truncated': len(rows) > len(selected), 'next_offset': next_offset, 'items': selected, 'note': 'ScienceDirect 官方字段搜索；源可能将宽泛总数截为1000000，分页排序可能变化。开放获取标志不证明学校逐篇订购或所有使用权限；同名作者需消歧。PII 可用于官方详情与可用摘要查询。'}
