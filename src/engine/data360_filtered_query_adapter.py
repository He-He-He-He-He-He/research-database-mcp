"""World Bank Data360 filtered observations, retaining dimensions and pagination."""
import release_runtime
import json, re, requests
from data360_metadata_adapter import disaggregations
BASE = 'https://data360api.worldbank.org/data360/data'
DOC = 'https://data360.worldbank.org/en/api'
FIELDS = {'SEX', 'AGE', 'URBANISATION', 'COMP_BREAKDOWN_1', 'COMP_BREAKDOWN_2', 'COMP_BREAKDOWN_3', 'FREQ', 'UNIT_MEASURE', 'UNIT_TYPE', 'UNIT_MULT'}

def query(dataset, indicator, country, start, end, filters=None, offset=0):
    for n, v in [('dataset', dataset), ('indicator', indicator)]:
        if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}', v):
            raise ValueError(n + ' 格式无效')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('国家代码须为三个大写字母')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份无效')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('偏移量超限')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > len(FIELDS) or any((k not in FIELDS for k in filters)):
        raise ValueError('无效维度字段')
    dims = disaggregations(dataset, indicator)['dimensions']
    available = {d['field_name']: d['field_value'] for d in dims}
    for k, v in filters.items():
        if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.+-]{1,100}', v):
            raise ValueError('维度代码无效')
        if k not in available or v not in [str(x) for x in available[k]]:
            raise ValueError('维度代码不在该指标当前官方分组目录中：' + k)
    params = {'DATABASE_ID': dataset, 'INDICATOR': indicator, 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end, 'skip': offset, **filters}
    with requests.get(BASE, params=params, timeout=35, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('官方数据入口返回跳转')
        r.raise_for_status()
        url = r.url
        parts = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 10000000:
                raise ValueError('响应过大，请缩小维度或年份')
            parts.append(b)
    data = json.loads(b''.join(parts))
    rows = data.get('value') if isinstance(data, dict) else None
    total = data.get('count') if isinstance(data, dict) else None
    if not isinstance(rows, list) or not isinstance(total, int):
        raise RuntimeError('数据响应结构异常')
    for row in rows:
        if any((str(row.get(k)) != str(v) for k, v in {'DATABASE_ID': dataset, 'INDICATOR': indicator, 'REF_AREA': country, **filters}.items())):
            raise RuntimeError('上游返回不符合筛选条件的观测')
    return {'source_url': url, 'documentation': DOC, 'dataset': dataset, 'indicator': indicator, 'country': country, 'filters': filters, 'offset': offset, 'total': total, 'returned': len(rows), 'next_offset': offset + len(rows) if rows and offset + len(rows) < total else None, 'rows': rows, 'note': '上游每次最多返回 1000 行，count 为总数、不是当前页数；数据更新时分页顺序可能变化。保留来源单位、倍数、状态和分组；代码存在不保证所有组合有数据。空结果不是零，历史值可能修订，详细定义请查看对应指标元数据。'}
