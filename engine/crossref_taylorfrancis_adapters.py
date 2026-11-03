"""Crossref 前缀 10.1080 中 Informa UK 登记的期刊文章公开题录。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/prefixes/10.1080/works'

def taylorfrancis_journal_metadata(query, page=1, page_size=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if not isinstance(page, int) or isinstance(page, bool) or (not isinstance(page_size, int)) or isinstance(page_size, bool) or (page < 1) or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    q = query.strip()
    r = requests.get(URL, params={'query': q, 'filter': 'type:journal-article', 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=25)
    r.raise_for_status()
    d = r.json().get('message', {})
    records = d.get('items')
    total = d.get('total-results')
    if not isinstance(records, list) or not isinstance(total, int):
        raise ValueError('Crossref 未返回可识别的结果')
    rows = []
    for x in records:
        publisher = x.get('publisher', '')
        titles = x.get('title', [])
        if not publisher.casefold().startswith('informa uk') or x.get('type') != 'journal-article' or (not titles):
            continue
        rows.append({'doi': x.get('DOI'), 'title': titles[0], 'journal': x.get('container-title'), 'publisher': publisher, 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL'), 'type': x['type']})
    return {'source': 'Crossref 前缀 10.1080 中 Informa UK 期刊文章元数据', 'source_url': URL, 'query': q, 'upstream_total': total, 'page': page, 'requested_page_size': page_size, 'items': rows, 'note': '上游总数为前缀 10.1080 的期刊文章匹配数，不是本地出版社筛选后的总数；一页可能不足或漏掉异名与其他前缀。非全部 Taylor & Francis 期刊、馆藏权限或全文。'}
