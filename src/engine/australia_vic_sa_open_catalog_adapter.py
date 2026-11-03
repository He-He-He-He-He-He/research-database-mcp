"""Australian Victorian and South Australian government open data catalogues, resource metadata and DataStore."""
import release_runtime
import re, json, requests
SITES = {'victoria': ('https://discover.data.vic.gov.au/api/3/action/', 'https://discover.data.vic.gov.au/'), 'south-australia': ('https://data.sa.gov.au/data/api/3/action/', 'https://data.sa.gov.au/')}

def _site(site):
    if site not in SITES:
        raise ValueError('site 须为 victoria 或 south-australia')
    return SITES[site]

def get(site, action, params):
    base, _ = _site(site)
    with requests.get(base + action, params=params, timeout=30, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('官方入口返回跳转，请核验')
        r.raise_for_status()
        parts = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 10000000:
                raise ValueError('结果过大，请缩小查询')
            parts.append(b)
    parsed = json.loads(b''.join(parts))
    if not parsed.get('success'):
        raise ValueError('官方目录未返回成功结果')
    return parsed['result']

def _id(x):
    if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_-]{1,150}', x):
        raise ValueError('无效数据集或资源 ID')
    return x

def _page(n, maximum, name):
    if isinstance(n, bool) or not isinstance(n, int) or (not 0 <= n <= maximum):
        raise ValueError(name + ' 超出范围')
    return n

def search(site, query, rows=10, start=0):
    base, doc = _site(site)
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1 至 200 字符')
    _page(rows, 30, '每页')
    _page(start, 10000, '起始位置')
    if rows < 1:
        raise ValueError('每页须至少 1 条')
    x = get(site, 'package_search', {'q': query, 'rows': rows, 'start': start})
    return {'site': site, 'source': base + 'package_search', 'documentation': doc, 'query': query, 'start': start, 'total': x.get('count'), 'results': x.get('results', []), 'note': '这是澳大利亚州级目录，包含不同机构、地方和年份，不代表全国统计或历史快照。请核对每项来源、地理范围、许可和资源可用性。'}

def detail(site, identifier, kind='package'):
    base, doc = _site(site)
    if kind not in ('package', 'resource'):
        raise ValueError('kind 须为 package 或 resource')
    action = kind + '_show'
    return {'site': site, 'source': base + action, 'documentation': doc, 'identifier': _id(identifier), 'result': get(site, action, {'id': identifier}), 'note': '目录详情列出资源及其 datastore_active 状态，不保证外链均可访问。元数据修改时间不等于数据观察期。'}

def data(site, resource_id, query='', limit=10, offset=0, filters=None):
    base, doc = _site(site)
    _id(resource_id)
    _page(limit, 100, '每页')
    _page(offset, 10000, '起始位置')
    if limit < 1:
        raise ValueError('每页须至少 1 条')
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('数据关键词无效')
    params = {'resource_id': resource_id, 'limit': limit, 'offset': offset}
    if query:
        params['q'] = query
    if filters is not None:
        if not isinstance(filters, dict) or len(filters) > 10:
            raise ValueError('过滤条件应为最多 10 项 JSON 对象')
        serialized = json.dumps(filters, ensure_ascii=False)
        if len(serialized) > 2000:
            raise ValueError('过滤条件过长')
        params['filters'] = serialized
    x = get(site, 'datastore_search', params)
    return {'site': site, 'source': base + 'datastore_search', 'documentation': doc, 'resource_id': resource_id, 'query': query, 'offset': offset, 'requested_limit': limit, 'result': x, 'note': '仅支持已发布到 CKAN DataStore 的资源；字段、数值和缺失标记原样保留。数据是否全国适用、时间、单位、版权由具体数据集决定。上游的总数与分页可能变化。'}
