"""Tianlu ancient-book institution IP catalog search; no text output."""
import release_runtime
import requests
BASE = 'https://tlgj.bbtpress.com/api-biz/'

def search(keyword, page=1, limit=5, session=None, category='', field='all'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    if not isinstance(category, str) or len(category) > 100 or any((ord(c) < 32 for c in category)):
        raise ValueError('分类须为不超过100字的单行文本')
    category = category.strip()
    fields = {'all': '0', 'title': '5', 'author': '4'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE + 'common/isCompanyUser', timeout=20)
    r.raise_for_status()
    j = r.json()
    identity = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 200 or (not isinstance(identity, dict)) or (identity.get('companyName') != '浙江大学'):
        raise RuntimeError('未确认浙江大学机构身份')
    b = {'keyword': q, 'pageNum': page, 'pageSize': limit, 'type': 0, 'searchType': '0' if field == 'all' else '1', 'sort': '1', 'sortType': 2, 'isOnlyPermit': 0, 'searchAccuracyType': 1, 'isInnerSearch': 0, 'textType': fields[field], 'isShowAll': True, 'categoryNames': [category] if category else [], 'dynastyNames': [], 'advaList': [], 'bookReadingListIds': '', 'bookIds': ''}
    r = s.post(BASE + 'search/bookList', json=b, timeout=30)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 200 or (not isinstance(d, dict)) or (d.get('keywordStr') != (q if field == 'all' else q + '~' + q + 'd')) or (type(d.get('bookTotalNum')) is not int) or (d['bookTotalNum'] < 0) or (type(d.get('totalNum')) is not int) or (not isinstance(d.get('bookList'), list)) or (len(d['bookList']) > limit):
        raise RuntimeError('检索响应异常')
    expected = min(limit, max(0, d['bookTotalNum'] - (page - 1) * limit))
    if len(d['bookList']) != expected:
        raise RuntimeError('站方返回书目条数与书数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['bookList']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('bookName'), str)):
            raise RuntimeError('书目编号或名称缺失')
        if category and (not isinstance(x.get('categoryName'), str) or not (x['categoryName'] == category or x['categoryName'].startswith(category + '/'))):
            raise RuntimeError('结果分类与筛选不一致')
        items.append({'id': x['id'], 'title': x['bookName'], 'classification': x.get('categoryName'), 'author': x.get('writer'), 'hit_count': x.get('hitNum'), 'permission_marker': x.get('isPermit')})
    result = {'source': '天禄云枢古籍数据库', 'institution': '浙江大学', 'institution_validity_date': identity.get('validityDate'), 'query': q, 'page': page, 'page_size': limit, 'book_total': d['bookTotalNum'], 'text_hit_total': d['totalNum'], 'items': items[:limit], 'note': '一般检索未限定有权限内容；命中书数与文本命中数不同，权限标记为原站值，不代表逐书阅读权限；不输出正文。'}
    result['note'] += ' 按书数与请求页次校验条数；站方不回显页码，数据可能变化。'
    if category:
        result['category_requested'] = category
        result['note'] += ' 站方未回显分类条件或页码，已逐项核对分类前缀；零结果不证明分类名称有效或该类无书。'
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 站方未回显检索字段或页码，匹配须逐项核对。'
    return result
