"""DRAA 精选集公开搜索题录；单次查询最多 20 条。"""
import release_runtime
import requests
URL = 'https://worldlibrary.ai/wl-api/search/search'
FIELDS = ['title', 'author', 'language', 'publisher', 'publication_year', 'collection', 'document_type', 'page']

def search_draa(keyword, limit=20):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('关键词不能为空')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 20):
        raise ValueError('limit 必须为 1–20')
    payload = {'search_type': 'keyword', 'query': keyword.strip(), 'size': limit, 'facet_size': 20, 'source_fields': FIELDS, 'facet': ['collection'], 'collection': ['draa']}
    response = requests.post(URL, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('hits'), list) or 'total' not in data:
        raise ValueError('上游搜索结果格式发生变化')
    return {'source': 'World Library DRAA 精选集', 'query': keyword.strip(), 'total': data['total'], 'items': [{'id': x.get('id'), 'metadata': x.get('source', {}), 'permission': x.get('permission', {}), 'url': f"https://worldlibrary.ai/book/draa/{x['id']}"} for x in data['hits'] if x.get('id')], 'note': '公开检索题录；实际阅读权限以网站为准，不代表浙大机构或全文授权。'}
