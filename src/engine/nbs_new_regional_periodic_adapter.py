"""NBS new provincial month/quarter and main-city monthly price series."""
import release_runtime
import re
import requests
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external/'
SCOPES = {'province_monthly': ('4', 'MM'), 'province_quarterly': ('5', 'SS'), 'city_monthly': ('7', 'MM')}

def _id(x):
    if not isinstance(x, str) or not re.fullmatch('[0-9a-f]{32}', x):
        raise ValueError('expected 32-character lowercase hexadecimal ID')
    return x

def _get(path, params):
    response = requests.get(BASE + path, params=params, timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get('success') is not True:
        raise RuntimeError('NBS request failed: ' + str(data.get('message')))
    return data['data']

def categories(scope, parent_id=''):
    if scope not in SCOPES:
        raise ValueError('unknown scope')
    if parent_id:
        _id(parent_id)
    return _get('new/queryIndexTreeAsync', {'pid': parent_id, 'code': SCOPES[scope][0]})

def indicators(category_id, keyword=''):
    return _get('new/queryIndicatorsByCid', {'cid': _id(category_id), 'dt': '', 'name': keyword})

def region_categories(category_id):
    return _get('getDaCatalogTreeByIndicatorCid', {'indicatorCid': _id(category_id)})

def regions(region_category_id):
    return _get('getDasByDaCatalogId', {'daCid': _id(region_category_id)})

def _period(value, suffix):
    pat = '(\\d{4})(0[1-9]|1[0-2])MM' if suffix == 'MM' else '(\\d{4})(0[1-4])SS'
    m = re.fullmatch(pat, value)
    if not m:
        raise ValueError('invalid period for selected scope')
    return tuple(map(int, m.groups()))

def series(scope, category_id, indicator_ids, region_category_id, region_code, start, end):
    if scope not in SCOPES:
        raise ValueError('unknown scope')
    if _period(start, SCOPES[scope][1]) > _period(end, SCOPES[scope][1]):
        raise ValueError('start must not exceed end')
    _id(category_id)
    _id(region_category_id)
    if isinstance(indicator_ids, str):
        indicator_ids = [indicator_ids]
    if not indicator_ids or len(indicator_ids) > 50 or len(indicator_ids) != len(set(indicator_ids)):
        raise ValueError('select 1 to 50 unique indicators')
    meta = indicators(category_id)
    index = {x['_id']: x for x in meta['list']}
    if any((i not in index for i in indicator_ids)):
        raise ValueError('indicator not in category')

    def tree_ids(nodes):
        for n in nodes:
            yield n['_id']
            yield from tree_ids(n.get('children') or [])
    if region_category_id not in set(tree_ids(region_categories(category_id))):
        raise ValueError('region category does not belong to indicator category')
    area = {x['name_value']: x for x in regions(region_category_id)}
    if not isinstance(region_code, str) or region_code not in area:
        raise ValueError('select exactly one valid region code')
    root = categories(scope)
    if len(root) != 1:
        raise RuntimeError('unexpected root response')
    body = {'cid': category_id, 'indicatorIds': indicator_ids, 'daCatalogId': '', 'das': [{'text': area[region_code]['name_text'], 'value': region_code}], 'showType': '1', 'dts': [start + '-' + end], 'rootId': _id(root[0]['_id'])}
    r = requests.post(BASE + 'stream/esData', json=body, timeout=90)
    r.raise_for_status()
    obj = r.json()
    if obj.get('success') is not True or not isinstance(obj.get('data'), list):
        raise RuntimeError('unexpected NBS response: ' + str(obj.get('message')))
    return {'source': '国家统计局国家数据新版地区时序', 'source_url': BASE + 'stream/esData', 'scope': scope, 'category_id': category_id, 'start': start, 'end': end, 'scope_note': 'scope 为请求的目录范围，尚未验证 category_id 属于该范围；请通过对应范围的目录树确认。以返回的地区和指标元数据为准。', 'region': area[region_code], 'indicators': [index[i] for i in indicator_ids], 'data': obj['data']}
