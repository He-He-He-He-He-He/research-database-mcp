"""NASA Technical Reports Server public citation search and detail."""
import release_runtime
import re
import requests
BASE = 'https://ntrs.nasa.gov/api/citations'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}
FIELDS = ('id', 'title', 'abstract', 'stiType', 'stiTypeDetails', 'distribution', 'distributionDate', 'created', 'modified', 'authorAffiliations', 'center', 'subjectCategories', 'keywords', 'publications', 'sourceIdentifiers', 'fundingNumbers', 'copyright', 'downloadsAvailable', 'onlyAbstract', 'related')

def _record(value):
    if not isinstance(value, dict) or value.get('distribution') != 'PUBLIC' or (not value.get('id')):
        raise ValueError('NASA 结果不是可验证的公开题录')
    return {k: value[k] for k in FIELDS if k in value}

def search(query, size=5, offset=0, session=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词不能为空且最多 200 字符')
    if type(size) is not int or not 1 <= size <= 20 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('分页参数无效')
    params = {'q': query.strip(), 'page': {'size': size, 'from': offset}}
    r = (session or requests).post(BASE + '/search', json=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('results'), list) or (not isinstance(d.get('stats'), dict)):
        raise ValueError('NASA 搜索返回格式异常')
    return {'source': 'NASA Technical Reports Server (NTRS), publicly available content', 'source_url': 'https://ntrs.nasa.gov/search/', 'api_documentation': 'https://ntrs.nasa.gov/api/openapi/', 'query': params, 'stats': d['stats'], 'items': [_record(x) for x in d['results']], 'note': '公开题录和摘要，不包括受限的 NTRS-R；公开可访问不等于全文均为公有领域，请分别核对版权及使用条件。'}

def detail(citation_id, session=None):
    if not re.fullmatch('\\d{8,14}', str(citation_id)):
        raise ValueError('NASA 题录 ID 格式无效')
    u = BASE + '/' + str(citation_id)
    r = (session or requests).get(u, headers=HEADERS, timeout=25)
    r.raise_for_status()
    d = _record(r.json())
    if str(d['id']) != str(citation_id):
        raise ValueError('NASA 题录 ID 不匹配')
    return {'source': 'NASA Technical Reports Server (NTRS), publicly available content', 'source_url': 'https://ntrs.nasa.gov/citations/' + str(citation_id), 'note': '仅公开题录；附件和全文各自的权利与访问条件需核查。', 'data': d}
