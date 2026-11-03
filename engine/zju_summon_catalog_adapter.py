"""浙江大学求是学术搜索公开聚合题录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://zju.summon.serialssolutions.com/api/search'

def search(keyword, page=1, limit=5, include_facets=False):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 25):
        raise ValueError('每页最多返回 25 条')
    if not isinstance(include_facets, bool):
        raise ValueError('include_facets 须为布尔值')
    q = keyword.strip()
    r = requests.get(URL, params={'q': q, 'pn': page, 'ps': limit}, timeout=30)
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('求是搜索未返回 JSON') from None
    query = d.get('query') if isinstance(d, dict) else None
    if not isinstance(query, dict) or query.get('original_query') != q or query.get('page_number') != page or (query.get('page_size') != limit) or (type(d.get('record_count')) is not int) or (d['record_count'] < 0) or (not isinstance(d.get('documents'), list)) or (len(d['documents']) > limit):
        raise RuntimeError('求是搜索查询、页码或响应结构异常')
    expected = min(limit, max(0, d['record_count'] - (page - 1) * limit))
    if len(d['documents']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['documents']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('title'), str)):
            raise RuntimeError('题录缺少编号或标题')
        authors = x.get('authors') or []
        databases = x.get('databases') or []
        if not isinstance(authors, list) or not isinstance(databases, list):
            raise RuntimeError('作者或来源数据库结构异常')
        item = {'id': x['id'], 'title': BeautifulSoup(x['title'], 'html.parser').get_text(' ', strip=True), 'authors': [a.get('fullname') for a in authors if isinstance(a, dict) and a.get('fullname')], 'content_type': x.get('content_type'), 'publisher': x.get('publisher'), 'publication_years_raw': x.get('publication_years'), 'publication_date_raw': x.get('publication_date'), 'dois_raw': x.get('dois'), 'isbns_raw': x.get('isbns'), 'issns_raw': x.get('issns'), 'database_names': [a.get('name') for a in databases if isinstance(a, dict) and a.get('name')], 'has_fulltext_raw': x.get('has_fulltext'), 'in_holdings_raw': x.get('in_holdings'), 'is_peer_reviewed_raw': x.get('is_peer_reviewed')}
        title = x['title']
        if re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', title, re.I):
            item['title_raw'] = None
            item['title_raw_omitted'] = True
            if re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:token|session|sid|apikey|api_key)\\s*=', item['title'], re.I):
                item['title'] = None
        else:
            item['title_raw'] = title
        items.append(item)
    result = {'source': '浙江大学求是学术搜索（Summon）聚合题录', 'query': q, 'page': page, 'page_size': limit, 'total': d['record_count'], 'total_pages_raw': d.get('page_count'), 'items': items[:limit], 'note': '学校专属发现服务聚合多个来源，结果及去重方式由上游决定；馆藏及全文标志是平台元数据，不证明逐条实际全文权限。仅查询题录；安全 title_raw 保留高亮，含链接或疑似凭据时省略并标记；按源总数和回显页次校验数量，数据可能变化。'}
    if include_facets:
        facets = d.get('facet_fields')
        if not isinstance(facets, list):
            raise RuntimeError('来源分面结构异常')
        result['facets'] = []
        for f in facets:
            if not isinstance(f, dict) or not isinstance(f.get('field_name'), str) or (not isinstance(f.get('counts'), list)):
                raise RuntimeError('来源分面结构异常')
            counts = []
            for c in f['counts']:
                if not isinstance(c, dict) or not isinstance(c.get('value'), str) or type(c.get('count')) is not int or (c['count'] < 0):
                    raise RuntimeError('来源分面计数结构异常')
                counts.append({'value': c['value'], 'count': c['count']})
            result['facets'].append({'field_name': f['field_name'], 'display_name': f.get('display_name'), 'has_more_facets_raw': f.get('has_more_facets'), 'counts': counts})
        result['note'] += ' 分面仅含站方当前返回的有限项，未给出 has_more 不能视为完整；全文和馆藏分面不证明逐篇权限。'
    return result
