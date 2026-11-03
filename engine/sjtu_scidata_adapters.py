"""上海交通大学科学数据平台公开记录的检索和元数据。"""
import release_runtime
import re
import requests
BASE = 'https://scidata.sjtu.edu.cn/api/records'

def _get(url, params=None):
    r = requests.get(url, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    return r.json()

def _record(x):
    if not x.get('is_published') or x.get('is_draft'):
        raise ValueError('只返回已发布记录')
    m = x.get('metadata', {})
    a = x.get('access', {})
    authors = [z.get('person_or_org', {}).get('name') for z in m.get('creators', []) if isinstance(z, dict)]
    return {'id': x.get('id'), 'title': m.get('title'), 'description': m.get('description'), 'publication_date': m.get('publication_date'), 'publisher': m.get('publisher'), 'subjects': [z.get('subject') for z in m.get('subjects', []) if isinstance(z, dict)], 'creators': authors, 'resource_type': m.get('resource_type', {}).get('id'), 'rights': m.get('rights', []), 'access': {'record': a.get('record'), 'files': a.get('files'), 'status': a.get('status')}, 'doi': x.get('pids', {}).get('doi', {}).get('identifier'), 'url': 'https://scidata.sjtu.edu.cn/records/' + str(x.get('id', ''))}

def sjtu_scidata_search(keyword, size=10, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(size, int)) or (not 1 <= size <= 50) or (not isinstance(page, int)) or (not 1 <= page <= 100):
        raise ValueError('请检查关键词、分页和每页数量')
    x = _get(BASE, {'q': keyword, 'size': size, 'page': page})
    hits = x.get('hits', {})
    if not isinstance(hits.get('hits'), list):
        raise ValueError('未识别搜索结果')
    return {'total': hits.get('total'), 'page': page, 'items': [_record(a) for a in hits['hits']]}

def sjtu_scidata_detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[a-z0-9]{5}-[a-z0-9]{5}', identifier):
        raise ValueError('请输入记录编号')
    return _record(_get(BASE + '/' + identifier))
