"""Documented Taiwan household administration open-data API (single page)."""
import release_runtime
import re
import requests
DOC = 'https://www.ris.gov.tw/rs-opendata/api/Main/docs/v1'
BASE = 'https://www.ris.gov.tw/rs-opendata/api/v1/datastore/'

def _paths():
    r = requests.get(DOC, timeout=25)
    r.raise_for_status()
    doc = r.json()
    return doc['paths']

def catalog(keyword=''):
    out = []
    for path, desc in _paths().items():
        m = re.fullmatch('/(ODRP\\d+)/\\{([^{}]+)\\}', path)
        get = desc.get('get', {})
        if not m or keyword not in get.get('summary', ''):
            continue
        out.append({'code': m.group(1), 'period_name': m.group(2), 'title': get.get('summary'), 'parameters': get.get('parameters', [])})
    return out

def query(code, period, page=1, county=None, town=None, village=None):
    if not re.fullmatch('ODRP\\d+', str(code)) or not re.fullmatch('\\d{1,8}', str(period)):
        raise ValueError('代码或日期格式不正确')
    if int(page) < 1:
        raise ValueError('页码须为正整数')
    entries = [x for x in catalog() if x['code'] == code]
    if len(entries) != 1:
        raise ValueError('该代码不在官方文档的一参数数据集中')
    params = {'PAGE': str(page)}
    for key, value in [('COUNTY', county), ('TOWN', town), ('VILLAGE', village)]:
        if value is not None:
            params[key] = value
    allowed = {p['name'] for p in entries[0]['parameters'] if p['in'] == 'query'}
    if not set(params) <= allowed:
        raise ValueError('该数据集不支持指定筛选参数')
    r = requests.get(BASE + code + '/' + str(period), params=params, timeout=35)
    r.raise_for_status()
    data = r.json()
    if data.get('responseCode') != 'OD-0101-S':
        raise RuntimeError('来源返回非成功状态: ' + str(data.get('responseMessage')))
    return {'dataset': entries[0]['title'], 'url': r.url, 'data': data, 'note': '只返回指定页；totalDataSize 可能为未筛选总量，以实际结果与分页为准。民国年加1911为公历年；注意登记人口口径。'}
