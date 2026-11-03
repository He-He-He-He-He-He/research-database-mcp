"""Crossref AIAA 注册成员公开期刊及会议文章题录。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/members/1387/works'
TYPES = {'journal': 'journal-article', 'conference': 'proceedings-article'}

def aiaa_metadata(query, kind='journal', page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if kind not in TYPES:
        raise ValueError('kind 须为 journal 或 conference')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    q = query.strip()
    typ = TYPES[kind]
    r = requests.get(URL, params={'query': q, 'filter': 'type:' + typ, 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    records = d.get('items')
    total = d.get('total-results')
    if not isinstance(records, list) or not isinstance(total, int):
        raise ValueError('Crossref 返回结构异常')
    rows = []
    for x in records:
        pub = x.get('publisher', '')
        title = x.get('title', [])
        if not pub.casefold().startswith('american institute of aeronautics and astronautics') or x.get('type') != typ or (not title):
            continue
        rows.append({'doi': x.get('DOI'), 'title': title[0], 'container': x.get('container-title'), 'publisher': pub, 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL'), 'relation': x.get('relation', {}), 'update_to': x.get('update-to', [])})
    return {'source': 'Crossref 成员 1387 的 AIAA 公开题录', 'source_url': URL, 'query': q, 'kind': kind, 'upstream_total': total, 'page': page, 'requested_page_size': page_size, 'items': rows, 'note': '总数为上游匹配数，本地出版社筛选后可能不足页数或遗漏异名。公开题录不证明学校订购、全文或机构权限；文献状态请核对原始记录。'}
