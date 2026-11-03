"""读取 Crossref 上 DOI 前缀 10.1061 的公开 ASCE 记录元数据。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/prefixes/10.1061/works'

def crossref_asce_search(keyword, page=1, page_size=10):
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
        if not doi.lower().startswith('10.1061/') or not title:
            raise ValueError('结果缺少 ASCE 前缀或标题')
        rows.append({'doi': doi, 'title': title[0], 'type': x.get('type'), 'publisher': x.get('publisher'), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref DOI 前缀 10.1061', 'source_url': URL, 'query': q, 'total': d['total-results'], 'page': page, 'items': rows, 'note': '限定 DOI 前缀的公开元数据，包含多种文献类型；非浙大全部馆藏、订购状态或全文。'}
