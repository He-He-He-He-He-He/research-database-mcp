"""Crossref Journal of Computer-Mediated Communication 单刊公开元数据，限定 ISSN 1083-6101。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/journals/1083-6101/works'

def crossref_jcmc_search(keyword, page=1, page_size=10):
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
        title = x.get('title', [])
        issns = x.get('ISSN', [])
        if '1083-6101' not in issns or not title:
            raise ValueError('结果未确认 Journal of Computer-Mediated Communication ISSN 或标题')
        rows.append({'doi': x.get('DOI'), 'title': title[0], 'type': x.get('type'), 'journal': x.get('container-title'), 'publisher': x.get('publisher'), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref Journal of Computer-Mediated Communication 单刊（ISSN 1083-6101）', 'source_url': URL, 'query': q, 'total': d['total-results'], 'page': page, 'items': rows, 'note': '单刊公开元数据、按相关性查询；非整个 Oxford 期刊库或浙大订购和全文权限。'}
