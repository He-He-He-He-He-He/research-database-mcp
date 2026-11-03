"""Ireland and Switzerland official open data catalogues: CKAN metadata search and detail."""
import release_runtime
import re, json, requests
SITES = {'ireland': ('https://data.gov.ie/api/3/action/', 'https://data.gov.ie/how-to-guides/developer-resources'), 'switzerland': ('https://ckan.opendata.swiss/api/3/action/', 'https://handbook.opendata.swiss/de/content/nutzen/api-nutzen.html')}

def get(site, action, params):
    if site not in SITES:
        raise ValueError('国家应为 ireland 或 switzerland')
    base, doc = SITES[site]
    with requests.get(base + action, params=params, timeout=30, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('上游返回跳转，请检查官方入口是否变化')
        r.raise_for_status()
        chunks = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > 10000000:
                raise ValueError('目录响应过大，请缩小结果范围')
            chunks.append(chunk)
    parsed = json.loads(b''.join(chunks))
    if not parsed.get('success'):
        raise RuntimeError('官方目录未返回成功结果')
    return (parsed['result'], base + action, doc)

def search(site, query, rows=10, start=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1 至 200 字符')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 30):
        raise ValueError('每页须为 1 至 30 条')
    if isinstance(start, bool) or not isinstance(start, int) or (not 0 <= start <= 10000):
        raise ValueError('起始位置限 0 至 10000')
    result, source, doc = get(site, 'package_search', {'q': query, 'rows': rows, 'start': start})
    return {'site': site, 'source': source, 'documentation': doc, 'query': query, 'start': start, 'rows_requested': rows, 'total': result.get('count'), 'results': result.get('results', []), 'caution': '当前官方目录提供的元数据覆盖不同发布者及地区，不代表全国完整数据或历史快照。搜索排序及查询由上游决定；资源链接、许可、数据时间和可用性须逐项核对。'}

def detail(site, identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_-]{1,150}', identifier):
        raise ValueError('数据集 ID 或名称无效')
    result, source, doc = get(site, 'package_show', {'id': identifier})
    return {'site': site, 'source': source, 'documentation': doc, 'identifier': identifier, 'result': result, 'caution': '仅为目录元数据，不保证每个资源可直接下载；元数据修改日期不等于数据观察期或历史发布时点。'}
