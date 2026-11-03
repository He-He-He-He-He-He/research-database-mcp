"""Search World Bank Data360 indicators and datasets through official public API."""
import release_runtime
import re, requests
URL = 'https://data360api.worldbank.org/data360/searchv2'
FIELDS = 'id,type,series_description/idno,series_description/name,series_description/database_id,series_description/database_name'

def search(keyword, kind='indicator', dataset='', limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('keyword must be 1–200 characters')
    if kind not in ('indicator', 'dataset'):
        raise ValueError('kind must be indicator or dataset')
    if not isinstance(dataset, str) or (dataset and (not re.fullmatch('[A-Za-z0-9_.-]{1,100}', dataset))):
        raise ValueError('invalid dataset code')
    if dataset and kind != 'indicator':
        raise ValueError('dataset filter applies to indicators only')
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('limit must be 1–50 and offset 0–10000')
    filt = "type eq '" + kind + "'"
    if dataset:
        filt += " and series_description/database_id eq '" + dataset + "'"
    payload = {'count': True, 'select': FIELDS, 'filter': filt, 'search': keyword, 'top': limit, 'skip': offset}
    with requests.post(URL, json=payload, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('search result exceeds 5 MB')
    j = __import__('json').loads(data)
    items = j.get('value') if isinstance(j, dict) else None
    total = j.get('@odata.count') if isinstance(j, dict) else None
    if not isinstance(items, list) or type(total) is not int or total < 0 or (len(items) > limit) or any((not isinstance(x, dict) or x.get('type') != kind for x in items)):
        raise RuntimeError('unexpected Data360 search response')
    if dataset and any(((x.get('series_description') or {}).get('database_id') != dataset for x in items)):
        raise RuntimeError('dataset filter mismatch')
    return {'source_url': URL, 'request': payload, 'total': total, 'offset': offset, 'returned': len(items), 'next_offset': offset + len(items) if items and offset + len(items) < total else None, 'items': items, 'note': '来源搜索引擎按相关度排序，实测不同 top/skip 请求排序和结果可能变化、跨页可能漏重，并非原子快照；关键词搜索结果不是覆盖率或权限证明。series_description 的指标和数据库代码可用于 Data360 通用数据查询；数据集搜索结果需核实来源元数据。'}
