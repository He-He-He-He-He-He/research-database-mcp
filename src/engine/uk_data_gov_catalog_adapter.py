"""UK government data directory: CKAN metadata search and detail."""
import release_runtime
import re, requests
BASE = 'https://ckan.publishing.service.gov.uk/api/action/'
DOC = 'https://guidance.data.gov.uk/get_data/api_documentation/'

def get(action, params):
    with requests.get(BASE + action, params=params, timeout=30, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > 10000000:
                raise ValueError('目录结果过大，请缩小结果范围')
            chunks.append(chunk)
    import json
    doc = json.loads(b''.join(chunks))
    if not doc.get('success'):
        raise RuntimeError('数据目录未返回成功结果')
    return doc['result']

def search(query, rows=10, start=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('搜索词须为 1 至 200 字符')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 30):
        raise ValueError('每页限 1 至 30 条')
    if isinstance(start, bool) or not isinstance(start, int) or (not 0 <= start <= 10000):
        raise ValueError('起始位置限 0 至 10000')
    result = get('package_search', {'q': query, 'rows': rows, 'start': start})
    return {'source': BASE + 'package_search', 'documentation': DOC, 'query': query, 'start': start, 'rows_requested': rows, 'total': result.get('count'), 'results': result.get('results', []), 'caution': '这是当前英国数据目录元数据，收录不同发布者与地区，不等同全部全国统计或历史快照；数据集可能撤换、重复或含第三方资源，需核对每项发布者、地区、时间、许可证和资源实际可用性。搜索语法及排序由上游决定。'}

def detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_-]{1,150}', identifier):
        raise ValueError('数据集 ID 或名称无效')
    return {'source': BASE + 'package_show', 'documentation': DOC, 'identifier': identifier, 'result': get('package_show', {'id': identifier}), 'caution': '仅返回目录元数据；资源链接及许可需逐项核验，记录修改日期不等于数据观察期或历史版本发布时间。'}
