"""NLM MedlinePlus official health-topic search; not individual medical advice."""
import release_runtime
import re
import xml.etree.ElementTree as ET
import requests
URL = 'https://wsearch.nlm.nih.gov/ws/query'

def _get(params):
    with requests.get(URL, params=params, timeout=30, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('NLM service returned HTTP ' + str(response.status_code))
        body = bytearray()
        for c in response.iter_content(65536):
            body.extend(c)
            if len(body) > 5000000:
                raise RuntimeError('NLM response exceeds 5 MB; reduce limit')
    root = ET.fromstring(body)
    if root.tag != 'nlmSearchResult' or root.find('error') is not None:
        raise RuntimeError('NLM search error or expired page; restart search')
    block = root.find('list')
    if block is None:
        raise RuntimeError('Unexpected NLM response; result list missing')
    items = []
    for doc in block.findall('document'):
        items.append({'rank': doc.get('rank'), 'url': doc.get('url'), 'content': [{'name': x.get('name'), 'value': ''.join(x.itertext())} for x in doc.findall('content')]})
    return {'source': 'MedlinePlus.gov, U.S. National Library of Medicine', 'source_info': 'https://medlineplus.gov/about/developers/webservices/', 'search_context': {k: root.findtext(k) for k in ('term', 'file', 'server', 'count', 'retstart', 'retmax')}, 'returned': len(items), 'items': items, 'note': 'MedlinePlus 健康主题资料；摘要和匹配标记可能含 HTML，链接及更新时间以原站为准，不替代针对个人的诊断或治疗。来源应注明 MedlinePlus.gov，不能暗示 NLM 为本工具背书；翻页文件可能过期。'}

def search(term, language='en', limit=5):
    if not isinstance(term, str) or not 1 <= len(term.strip()) <= 150:
        raise ValueError('Search term must contain 1–150 characters')
    if language not in ('en', 'es'):
        raise ValueError('Language must be en or es')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('Invalid limit')
    return _get({'db': 'healthTopics' if language == 'en' else 'healthTopicsSpanish', 'term': term, 'retmax': limit, 'tool': 'zju_research_toolkit'})

def next_page(file, server, start, limit=5):
    if not isinstance(file, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', file) or (not isinstance(server, str)) or (not re.fullmatch('[A-Za-z0-9_-]{1,100}', server)):
        raise ValueError('Invalid NLM pagination token')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, limit))) or start < 0 or (not 1 <= limit <= 20):
        raise ValueError('Invalid pagination')
    return _get({'file': file, 'server': server, 'retstart': start, 'retmax': limit, 'tool': 'zju_research_toolkit'})
