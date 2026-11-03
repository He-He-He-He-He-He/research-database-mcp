"""AMA Manual of Style 第十版的 Crossref 公开书目，不包含指导手册正文。"""
import release_runtime
import requests
URL = 'https://api.crossref.org/works'
DOI_PREFIX = '10.1093/jama/9780195176339.'

def ama_tenth_metadata(query, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    q = query.strip()
    params = {'query.container-title': 'AMA Manual of Style', 'query.title': q, 'filter': 'prefix:10.1093', 'rows': page_size, 'offset': (page - 1) * page_size}
    r = requests.get(URL, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json().get('message', {})
    items, total = (data.get('items'), data.get('total-results'))
    if not isinstance(items, list) or not isinstance(total, int):
        raise ValueError('Crossref 返回结构异常')
    found = []
    for item in items:
        doi, titles = (item.get('DOI', ''), item.get('title', []))
        if not doi.lower().startswith(DOI_PREFIX) or not titles:
            continue
        found.append({'doi': doi, 'title': titles[0], 'container_title': item.get('container-title', []), 'published': item.get('published', {}).get('date-parts'), 'url': item.get('URL')})
    return {'source': 'Crossref 公开题录，按第十版 ISBN 的 DOI 前缀筛选', 'source_url': URL, 'query': q, 'page': page, 'requested_page_size': page_size, 'upstream_total': total, 'items': found, 'note': '上游总数包含牛津其他内容，不是第十版匹配数；筛选在每个上游分页之后，页内可能不足或为空，且相关度检索可能漏项。馆方介绍第十版不证明当前具体版本或全文权限；本接口不提供手册正文。'}
