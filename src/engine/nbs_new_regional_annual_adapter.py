"""NBS new regional annual time-series; province and main city scopes."""
import release_runtime
import re
import requests
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external/'
SCOPES = {'province': '6', 'city': '8'}

def _id(x):
    if not isinstance(x, str) or not re.fullmatch('[0-9a-f]{32}', x):
        raise ValueError('expected 32-character lowercase hexadecimal ID')
    return x

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    if j.get('success') is not True:
        raise RuntimeError('NBS request failed: ' + str(j.get('message')))
    return j['data']

def categories(scope, parent_id=''):
    if scope not in SCOPES:
        raise ValueError('scope must be province or city')
    if parent_id:
        _id(parent_id)
    return _get('new/queryIndexTreeAsync', {'pid': parent_id, 'code': SCOPES[scope]})

def indicators(category_id, start_year, end_year, keyword=''):
    if type(start_year) is not int or type(end_year) is not int or (not 1900 <= start_year <= end_year <= 2100):
        raise ValueError('years must be integers in ascending order between 1900 and 2100')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    return _get('new/queryIndicatorsByCid', {'cid': _id(category_id), 'dt': f'{start_year}-{end_year}', 'name': keyword})

def region_categories(category_id):
    return _get('getDaCatalogTreeByIndicatorCid', {'indicatorCid': _id(category_id)})

def regions(region_category_id):
    return _get('getDasByDaCatalogId', {'daCid': _id(region_category_id)})

def series(scope, category_id, indicator_ids, region_category_id, region_codes, start_year, end_year):
    if scope not in SCOPES or not (isinstance(start_year, int) and isinstance(end_year, int) and (1900 <= start_year <= end_year <= 2100)):
        raise ValueError('invalid scope or year range')
    _id(category_id)
    _id(region_category_id)
    if isinstance(indicator_ids, str):
        indicator_ids = [indicator_ids]
    if isinstance(region_codes, str):
        region_codes = [region_codes]
    if not indicator_ids or len(indicator_ids) > 50 or len(indicator_ids) != len(set(indicator_ids)):
        raise ValueError('select 1 to 50 unique indicators')
    if len(region_codes) != 1:
        raise ValueError('select exactly one region; the upstream response only returned the first when multiple were requested')
    meta = indicators(category_id, start_year, end_year)
    index = {i['_id']: i for i in meta['list']}
    if any((i not in index for i in indicator_ids)):
        raise ValueError('indicator not found for requested category and years')

    def ids(nodes):
        for n in nodes:
            yield n['_id']
            yield from ids(n.get('children') or [])
    if region_category_id not in set(ids(region_categories(category_id))):
        raise ValueError('region category does not belong to selected indicator category')
    area = {x['name_value']: x for x in regions(region_category_id)}
    if any((i not in area for i in region_codes)):
        raise ValueError('region not found in selected region category')
    root = categories(scope)
    if len(root) != 1:
        raise RuntimeError('unexpected root response')
    body = {'cid': category_id, 'indicatorIds': indicator_ids, 'daCatalogId': '', 'das': [{'text': area[i]['name_text'], 'value': i} for i in region_codes], 'showType': '1', 'dts': [f'{start_year}YY-{end_year}YY'], 'rootId': _id(root[0]['_id'])}
    r = requests.post(BASE + 'stream/esData', json=body, timeout=90)
    r.raise_for_status()
    obj = r.json()
    if obj.get('success') is not True or not isinstance(obj.get('data'), list):
        raise RuntimeError('unexpected NBS data response: ' + str(obj.get('message')))
    return {'source': '国家统计局国家数据新版地区年度数据', 'source_url': BASE + 'stream/esData', 'scope': scope, 'category_id': category_id, 'start_year': start_year, 'end_year': end_year, 'scope_note': 'scope 为请求的目录范围，尚未验证 category_id 属于该范围；请通过对应范围的目录树确认。以返回的地区和指标元数据为准。', 'region_category_id': region_category_id, 'regions': [area[i] for i in region_codes], 'indicators': [index[i] for i in indicator_ids], 'data': obj['data']}
