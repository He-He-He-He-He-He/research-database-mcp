"""SpringerMaterials 的公开搜索题录；不获取数据表或全文。"""
import release_runtime
import json
import requests
from urllib.parse import urljoin
URL = 'https://smat-newsearch-api-prod.apps.public.k8s.springernature.io/search'
FACETS = {'properties': [], 'substances': [], 'substance_classes': [], 'substance_class_operator': 'OR', 'elementSystems': [], 'updated_property_value_ranges': [], 'datasources': [], 'datatypes': [], 'includeSubProperties': True}

def search_materials(query, limit=20, page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 200 or any((ord(c) < 32 for c in query)):
        raise ValueError('关键词须为 1–200 字单行文本')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 20):
        raise ValueError('limit 须为 1–20')
    if type(page) is not int or not 1 <= page <= 5000:
        raise ValueError('page 须为 1–5000')
    r = requests.get(URL, params={'query': query.strip(), 'pageStart': page, 'pageLength': limit, 'sortBy': 'relevance', 'selectedFacets': json.dumps(FACETS, separators=(',', ':'))}, timeout=20)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('hits'), list) or len(d['hits']) > limit or type(d.get('num_hits')) is not int or (d['num_hits'] < 0):
        raise ValueError('搜索结果格式变化')
    items = []
    for hit in d['hits']:
        if not hit.get('doc_id') or not str(hit.get('page_link', '')).startswith('/') or str(hit.get('page_link', '')).startswith('//'):
            raise ValueError('上游条目缺少标识或链接')
        items.append({k: hit.get(k) for k in ('doc_id', 'title', 'snippet', 'database_id', 'data_type', 'collection_type', 'page_link')})
        items[-1]['url'] = urljoin('https://materials.springer.com', hit['page_link'])
    return {'source': 'SpringerMaterials 搜索题录', 'query': query.strip(), 'page_requested': page, 'page_size_requested': limit, 'total': d['num_hits'], 'items': items, 'note': '公开搜索题录，源站未回显页码；越过末页可返回空列表。非材料属性数值或全文，网页结果不证明学校订购或逐篇访问权限。'}
