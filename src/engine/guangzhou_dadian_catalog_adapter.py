"""Guangzhou Library's Guangzhou Dadian public catalog search."""
import release_runtime
import re
import requests
BASE = 'https://gzdd.gzlib.org.cn/'
FIELDS = ('TITLE', 'RESPONSIBILITY', 'EDITION', 'CATALOG', 'COLLECTIONUNITS')

def _clean(s):
    return s.replace('###', '').replace('$$$', '') if isinstance(s, str) else None

def search(keyword, page=1, limit=5, session=None, field='all', author=''):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    fields = {'all': FIELDS, 'title': ('TITLE',), 'author': ('RESPONSIBILITY',), 'edition': ('EDITION',), 'catalog': ('CATALOG',), 'collection': ('COLLECTIONUNITS',)}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    if not isinstance(author, str) or len(author) > 100 or any((ord(c) < 32 for c in author)):
        raise ValueError('作者须为不超过 100 字的单行文本')
    author = author.strip()
    if author and field != 'title':
        raise ValueError('作者组合仅支持题名字段')
    q = keyword.strip()
    s = session or requests.Session()
    home = s.get(BASE + 'website/index', timeout=20)
    home.raise_for_status()
    body = {'pageIndex': page, 'pageSize': limit, 'sortField': 'relevant', 'sortType': 'desc', 'navis': [], 'conditions': [{'name': v, 'value': q, 'searchType': '%', 'logic': 'or'} for v in fields[field]]}
    if author:
        body['conditions'].append({'name': 'RESPONSIBILITY', 'value': author, 'searchType': '%', 'logic': 'and'})
    r = s.post(BASE + 'api/Search/Search', json=body, headers={'Referer': BASE + 'website/gzddDatabase'}, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('Data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('Code') != 1 or (not isinstance(d, dict)) or (d.get('PageIndex') != page) or (d.get('PageSize') != limit) or (type(d.get('Total')) is not int) or (not isinstance(d.get('DataList'), list)) or (len(d['DataList']) > limit):
        raise RuntimeError('原站返回异常')
    expected = min(limit, max(0, d['Total'] - (page - 1) * limit))
    if d['Total'] < 0 or len(d['DataList']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for row in d['DataList']:
        if not isinstance(row, dict) or not isinstance(row.get('BookId'), str) or (not isinstance(row.get('Title'), str)):
            raise RuntimeError('书目缺少编号或标题')
        raw = {k: row.get(k) for k in ('Title', 'Responsibility', 'Section', 'Catalog', 'BookNum', 'Edition')}
        if any((v is not None and (not isinstance(v, str) or re.search('(?i)https?://|(?:token|session|apikey|api_key)\\s*[=:]', v)) for v in raw.values())):
            raise RuntimeError('站方题录原字段格式异常')
        items.append({'source_fields_raw': raw, 'id': row['BookId'], 'title': _clean(row['Title']), 'responsibility': _clean(row.get('Responsibility')), 'division': _clean(row.get('Section')), 'series': _clean(row.get('Catalog')), 'volume': _clean(row.get('BookNum')), 'edition': _clean(row.get('Edition'))})
    result = {'source': '广州大典数据库', 'query': q, 'page': page, 'page_size': limit, 'total': d['Total'], 'items': items[:limit], 'note': '广州图书馆原站书目，按题名、责任者、版本、目录和收藏单位关联检索；未确认浙江大学机构身份和影像权限。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] = '广州图书馆原站单字段书目搜索；站方不回显字段条件，匹配可能涉及繁简转换，收藏单位未逐条核验；未确认浙江大学机构身份和影像权限。'
    if author:
        result['author_requested'] = author
        result['note'] += ' 题名与责任者按 AND 请求，站方不回显条件；已抽验样本，逐项匹配仍须核对。'
    result['note'] += ' source_fields_raw 保留站方题录原值，###/$$$ 为样本中的高亮标记；清理字段移除了这些标记。'
    return result
