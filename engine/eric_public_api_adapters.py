"""美国 IES ERIC 教育文献公开 API，单页题录。"""
import release_runtime
import html
import re
import requests
URL = 'https://api.ies.ed.gov/eric/'

def eric_public_search(query, page=1, page_size=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if not isinstance(page, int) or isinstance(page, bool) or (not isinstance(page_size, int)) or isinstance(page_size, bool) or (page < 1) or (not 1 <= page_size <= 50):
        raise ValueError('页码须大于零，每页 1–50 条')
    q = query.strip()
    r = requests.get(URL, params={'search': q, 'format': 'json', 'start': (page - 1) * page_size, 'rows': page_size}, timeout=25)
    r.raise_for_status()
    d = r.json().get('response', {})
    docs = d.get('docs')
    total = d.get('numFound')
    if not isinstance(docs, list) or not isinstance(total, int):
        raise ValueError('ERIC 返回结构不完整')

    def clean(x):
        if isinstance(x, str):
            return html.unescape(x)
        if isinstance(x, list):
            return [clean(y) for y in x]
        return x
    items = []
    for x in docs:
        if not re.fullmatch('(?:EJ|ED)\\d+', str(x.get('id', ''))) or not x.get('title'):
            raise ValueError('题录 ID 或标题不合法')
        items.append({k: clean(x.get(k)) for k in ('id', 'title', 'author', 'subject', 'publicationtype', 'publicationdateyear', 'language', 'publisher', 'peerreviewed')})
        items[-1]['record_url'] = 'https://eric.ed.gov/?id=' + x['id']
    return {'source': 'ERIC 美国教育资源信息中心公开 API', 'source_url': URL, 'query': q, 'total': total, 'page': page, 'page_size': page_size, 'items': items, 'note': 'ERIC 教育研究题录；检索语法及相关性由上游决定，非浙大机构授权或逐篇全文可用性。'}
