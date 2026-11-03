"""Read CADAL map catalog detail from a fresh, explicitly selected search result."""
import release_runtime
import re
import requests
from cadal_collections_catalog_adapter import URL, COLLECTIONS, _field, _clean
DETAIL_URL = 'https://tecang.cadal.edu.cn/metadata/api/tsk/port/v1.0/get'
FIELDS = ('title', 'creator', 'language', 'year', 'scale', 'height', 'width', 'publisher', 'source', 'mustid', 'subject', 'format', 'edition', 'general note', 'alternative title')
_UNSAFE = re.compile('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', re.I)

def detail(keyword, record_id, page=1, limit=10, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or '^^' in keyword:
        raise ValueError('关键词须为 1–100 字且不能包含 ^^')
    if isinstance(record_id, bool) or not str(record_id).isdigit() or int(record_id) <= 0:
        raise ValueError('记录编号须为正整数')
    if type(page) is not int or page < 1 or type(limit) is not int or (not 1 <= limit <= 30):
        raise ValueError('页码须为正整数，每页最多30条')
    s = session or requests.Session()
    body = {'dbname': COLLECTIONS['maps'], 'collectionSearchType': 'onecollectionsearch', 'curpage': page, 'pagesize': limit, 'sfields': ['all^^' + keyword.strip() + '^^wildcard'], 'sortWord': ['hitcount:1']}
    r = s.post(URL, json=body, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 200 or (not isinstance(d, dict)) or (not isinstance(d.get('dataTablemaps'), list)) or (type(d.get('total')) is not int):
        raise RuntimeError('地图检索响应异常')
    source_total = d['total']
    matches = [x for x in d['dataTablemaps'] if isinstance(x, dict) and str(_field(x.get('notDisplayed'), 'docid')) == str(record_id)]
    if len(matches) != 1:
        raise ValueError('指定记录不在当前搜索页或编号不唯一，请重新检索后选择')
    item = matches[0]
    nd = item.get('notDisplayed')
    title = _clean(_field(item.get('custom'), 'title'))
    db = _field(nd, 'dbname')
    opaque = _field(nd, 'dbinfo')
    if not isinstance(title, str) or not title or (not isinstance(db, str)) or (not isinstance(opaque, str)) or (not opaque):
        raise RuntimeError('搜索结果缺少详情所需字段')
    r = s.post(DETAIL_URL, data={'dbinfo': opaque, 'objectViewType': 'noiiif'}, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 200 or (not isinstance(d, list)) or (len(d) < 2) or (not all((isinstance(x, list) for x in d[:2]))):
        raise RuntimeError('地图详情响应异常')

    def fields(items):
        return {v.get('fieldname'): v.get('fieldvalue') for v in items if isinstance(v, dict) and isinstance(v.get('fieldname'), str)}
    shown, identity = (fields(d[0]), fields(d[1]))
    if str(identity.get('docid')) != str(record_id) or identity.get('dbname') != db or _clean(shown.get('title')) != title:
        raise RuntimeError('详情与所选记录不一致，请重新检索')
    result = {}
    omitted = []
    for key in FIELDS:
        val = shown.get(key)
        if val is None:
            continue
        if not isinstance(val, str) or _UNSAFE.search(val):
            omitted.append(key)
            continue
        result[key] = _clean(val)
    return {'source': 'CADAL 古代地图专题', 'query': keyword.strip(), 'page': page, 'page_size': limit, 'source_total': source_total, 'id': str(record_id), 'database': db, 'fields': result, 'omitted_fields': omitted, 'note': '详情按同一次搜索页记录关联并校验编号、库名及标题；排序可能变化，未读取影像，学校订购及全文权限未验证。'}
