"""长煦书馆平台公开题录搜索。"""
import release_runtime
import re
import requests
URL = 'https://portal.igpublish.com.cn/igp-api/public/organization/work-search'

def search(keyword, page=1, limit=5, product='', include_products=False, facet='', facet_value=''):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('每页须为 1–20 条')
    if not isinstance(product, str) or len(product) > 100 or re.search('[\\x00-\\x1f]', product):
        raise ValueError('产品名称须为不超过 100 字的单行文本')
    if not isinstance(include_products, bool):
        raise ValueError('include_products 须为布尔值')
    choices = {'year': ('filterByPublicationYears', 'publication_year'), 'subject': ('filterBySubjects', 'subjects'), 'publisher': ('filterByPublishers', 'original_publisher'), 'language': ('filterByLanguages', 'language'), 'type': ('filterByMaterialTypes', 'resource_type'), 'series': ('filterBySeries', 'series')}
    if facet not in ('', *choices):
        raise ValueError('分面须为 year、subject、publisher、language、type 或 series')
    if not isinstance(facet_value, str) or len(facet_value) > 200 or re.search('[\\x00-\\x1f]', facet_value):
        raise ValueError('分面值须为单行文本')
    facet_value = facet_value.strip()
    if facet_value and (not facet):
        raise ValueError('分面值须指定分面类别')
    if product and facet_value:
        raise ValueError('产品与其他分面组合尚未验证')
    q = keyword.strip()
    product = product.strip()
    payload = {'pageNum': page, 'pageSize': limit, 'keywords': q, 'lang': 'en'}
    if product:
        payload['filterByProducts'] = product
    if facet_value:
        payload[choices[facet][0]] = facet_value
    r = requests.post(URL, json=payload, timeout=30)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('长煦书馆未返回 JSON') from None
    d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(d, dict) or type(d.get('total')) is not int or d['total'] < 0 or (d.get('pageNum') != page) or (d.get('pageSize') != limit) or (not isinstance(d.get('items'), list)) or (len(d['items']) > limit):
        raise RuntimeError('书目响应、总数或分页异常')
    expected = min(limit, max(0, d['total'] - (page - 1) * limit))
    if len(d['items']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    if product:
        facets = d.get('facets', {}).get('products', []) if isinstance(d.get('facets'), dict) else []
        if not isinstance(facets, list) or not any((isinstance(x, dict) and x.get('label') == product and (x.get('cnt') == d['total']) for x in facets)):
            raise RuntimeError('原站未确认产品筛选及数量')
    selected_facets = None
    if facet:
        selected_facets = d.get('facets', {}).get(choices[facet][1]) if isinstance(d.get('facets'), dict) else None
        if not isinstance(selected_facets, list):
            raise RuntimeError('站方分面结构异常')
        for x in selected_facets:
            if not isinstance(x, dict) or not isinstance(x.get('label'), str) or type(x.get('cnt')) is not int or (x['cnt'] < 0):
                raise RuntimeError('站方分面条目异常')
        if facet_value and d['total'] > 0 and (not any((x['label'] == facet_value and x['cnt'] == d['total'] for x in selected_facets))):
            raise RuntimeError('站方未确认分面筛选数量')
    items = []
    for x in d['items']:
        if not isinstance(x, dict) or not isinstance(x.get('code'), str) or (not isinstance(x.get('title'), str)):
            raise RuntimeError('题录缺少编号或标题')
        p = x.get('permission') or {}
        if not isinstance(p, dict):
            raise RuntimeError('权限字段结构异常')
        items.append({'code': x['code'], 'title': x['title'], 'authors_raw': x.get('author'), 'publisher_raw': x.get('original_publisher'), 'publication_year': x.get('publication_year'), 'print_isbn_raw': x.get('pisbn13'), 'pdf_isbn_raw': x.get('isbn13_pdf'), 'resource_type_raw': x.get('resource_type'), 'product_codes_raw': x.get('dtbs_codes'), 'permission_flags_raw': {k: p.get(k) for k in ('preview', 'read', 'fullText', 'listen')}})
    result = {'source': '长煦书馆平台公开题录', 'query': q, 'product_filter_raw': product or None, 'page': page, 'page_size': limit, 'total': d['total'], 'items': items, 'note': '平台全站公开搜索；筛选零结果时原站可能回显不存在的产品名，不能据此验证产品名称有效、产品无书或学校未订购。未确认浙大机构身份或学校购买范围；权限标志仅为本次匿名响应，非持久或逐项全文许可证明；已按总数与回显页次核对条数，数据可能变化。'}
    if include_products:
        raw = d.get('facets', {}).get('products') if isinstance(d.get('facets'), dict) else None
        if not isinstance(raw, list):
            raise RuntimeError('产品分面结构异常')
        entries = []
        for entry in raw:
            if not isinstance(entry, dict) or not isinstance(entry.get('label'), str) or type(entry.get('cnt')) is not int or (entry['cnt'] < 0):
                raise RuntimeError('产品分面条目异常')
            entries.append({'label': entry['label'], 'count': entry['cnt']})
        result['product_facets'] = entries
        result['note'] += ' 产品分面可能被站方截断；数量为当前查询的站方统计，产品可重复覆盖，不能相加推算总数。'
    if facet:
        result['selected_facet'] = {'kind': facet, 'value_requested': facet_value or None, 'values': [{'label': x['label'], 'count': x['cnt']} for x in selected_facets]}
        result['note'] += ' 分面可能被截断，计数按站方口径；零结果无法验证筛选值有效或资料不存在，逐条相关性和权限未核。'
    return result
