"""Crossref 对 Bentham Science 注册成员的公开期刊文章题录。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/members/965/works'

def bentham_metadata(query, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    q = query.strip()
    r = requests.get(URL, params={'query': q, 'filter': 'type:journal-article', 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    if not isinstance(items, list) or not isinstance(total, int):
        raise ValueError('Crossref 返回结构异常')
    rows = []
    for x in items:
        publisher = x.get('publisher', '')
        titles = x.get('title', [])
        if not publisher.casefold().startswith('bentham science') or x.get('type') != 'journal-article' or (not titles):
            continue
        rows.append({'doi': x.get('DOI'), 'title': titles[0], 'journal': x.get('container-title'), 'publisher': publisher, 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL'), 'relation': x.get('relation', {}), 'update_to': x.get('update-to', [])})
    return {'source': 'Crossref 成员 965 中 Bentham Science 期刊文章公开元数据', 'source_url': URL, 'query': q, 'upstream_total': total, 'page': page, 'requested_page_size': page_size, 'items': rows, 'note': '总数为成员期刊文章上游匹配数；本地出版社筛选后可能不足页数或遗漏异名。公开题录不证明浙大订购、全文或机构权限；撤稿状态须核对原始记录。'}
