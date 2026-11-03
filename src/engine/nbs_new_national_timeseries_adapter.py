"""National Bureau of Statistics new national time-series explorer (public)."""
import release_runtime
import re
import requests
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external/'
CODES = {'monthly': '1', 'quarterly': '2', 'annual': '3'}
ID = re.compile('^[0-9a-f]{32}$')

def _id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError('Expected a 32-character lowercase hexadecimal identifier')
    return value

def _frequency(frequency):
    if frequency not in CODES:
        raise ValueError('frequency must be monthly, quarterly, or annual')
    return CODES[frequency]

def _get(path, params):
    response = requests.get(BASE + path, params=params, timeout=45)
    response.raise_for_status()
    obj = response.json()
    if obj.get('success') is not True:
        raise RuntimeError('NBS request failed: ' + str(obj.get('message')))
    return obj['data']

def categories(frequency, parent_id=''):
    """Return immediate child nodes; call with empty parent_id for the root."""
    if parent_id:
        _id(parent_id)
    return _get('new/queryIndexTreeAsync', {'pid': parent_id, 'code': _frequency(frequency)})

def indicators(category_id, keyword=''):
    """List metadata, including names, units and source annotations for a leaf."""
    return _get('new/queryIndicatorsByCid', {'cid': _id(category_id), 'dt': '', 'name': keyword})

def _period(value, frequency):
    patterns = {'annual': '(\\d{4})YY', 'monthly': '(\\d{4})(0[1-9]|1[0-2])MM', 'quarterly': '(\\d{4})(0[1-4])SS'}
    m = re.fullmatch(patterns[frequency], value)
    if not m:
        raise ValueError('Invalid period for ' + frequency)
    return tuple(map(int, m.groups()))

def series(frequency, category_id, indicator_ids, start, end):
    """Query nationwide observations; dates are inclusive NBS period codes."""
    _frequency(frequency)
    _id(category_id)
    if _period(start, frequency) > _period(end, frequency):
        raise ValueError('start must not exceed end')
    if isinstance(indicator_ids, str):
        indicator_ids = [indicator_ids]
    if not indicator_ids or len(indicator_ids) > 50 or len(set(indicator_ids)) != len(indicator_ids):
        raise ValueError('Supply 1 to 50 unique indicator IDs')
    for item in indicator_ids:
        _id(item)
    metadata = indicators(category_id)
    available = {item['_id']: item for item in metadata['list']}
    if any((item not in available for item in indicator_ids)):
        raise ValueError('Indicator missing from category metadata; verify category and identifier')
    roots = categories(frequency)
    if len(roots) != 1:
        raise RuntimeError('Unexpected frequency root response')
    payload = {'cid': category_id, 'indicatorIds': indicator_ids, 'daCatalogId': '', 'das': [{'text': '全国', 'value': '000000000000'}], 'showType': '1', 'dts': [start + '-' + end], 'rootId': _id(roots[0]['_id'])}
    response = requests.post(BASE + 'stream/esData', json=payload, timeout=90)
    response.raise_for_status()
    result = response.json()
    if result.get('success') is not True or not isinstance(result.get('data'), list):
        raise RuntimeError('Unexpected NBS data response: ' + str(result.get('message')))
    return {'source': '国家统计局国家数据新版全国时间序列', 'source_url': BASE + 'stream/esData', 'frequency': frequency, 'category_id': category_id, 'start': start, 'end': end, 'frequency_note': 'frequency 为请求的频率，尚未验证 category_id 是否属于该频率目录；请通过对应目录树及指标注释核实统计口径。', 'area': '全国', 'indicators': [available[i] for i in indicator_ids], 'data': result['data']}
