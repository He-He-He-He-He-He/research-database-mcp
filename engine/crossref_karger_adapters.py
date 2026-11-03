"""Crossref 前缀 10.1159 当前页的 S. Karger AG 公开元数据。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/prefixes/10.1159/works'

def crossref_karger_search(keyword, page=1, page_size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为1–200字')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页1至20条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    q = keyword.strip()
    r = requests.get(URL, params={'query': q, 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=20)
    r.raise_for_status()
    d = r.json().get('message', {})
    if 'items' not in d or 'total-results' not in d:
        raise ValueError('Crossref 未返回可识别结果')
    rows = []
    for x in d['items']:
        doi = x.get('DOI', '')
        title = x.get('title', [])
        publisher = x.get('publisher', '')
        if not doi.lower().startswith('10.1159/'):
            raise ValueError('结果不属于指定 DOI 前缀')
        if title and publisher.strip().casefold() == 's. karger ag':
            rows.append({'doi': doi, 'title': title[0], 'type': x.get('type'), 'publisher': publisher, 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref 前缀 10.1159 当前页 S. Karger AG 记录', 'source_url': URL, 'query': q, 'upstream_prefix_total': d['total-results'], 'page': page, 'items': rows, 'note': '只保留当前页出版商字段等于 S. Karger AG 的记录；上游前缀总数不等于本地筛选总数，不代表学校订购或全文。'}
