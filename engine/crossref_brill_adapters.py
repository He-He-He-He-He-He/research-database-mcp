"""Crossref DOI 前缀 10.1163 当前结果页中出版商标示为 BRILL 的公开元数据。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/prefixes/10.1163/works'

def crossref_brill_search(keyword, page=1, page_size=10):
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
        if not doi.lower().startswith('10.1163/'):
            raise ValueError('结果不属于指定 DOI 前缀')
        if title and publisher.strip().casefold() == 'brill':
            rows.append({'doi': doi, 'title': title[0], 'type': x.get('type'), 'publisher': publisher, 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref 前缀 10.1163 当前页标示 BRILL 的记录', 'source_url': URL, 'query': q, 'upstream_prefix_total': d['total-results'], 'page': page, 'items': rows, 'note': '本地只保留出版商字段等于 BRILL 的当前页记录；上游总数包含其他出版商，非筛选后总数。相关性检索不等于逐词匹配，不代表浙大订购或全文。'}
