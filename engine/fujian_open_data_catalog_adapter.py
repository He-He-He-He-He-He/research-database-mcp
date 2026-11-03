"""福建省公共数据资源开放目录及普遍开放的官网样本预览。"""
import release_runtime
import re
import requests
BASE = 'https://data.fujian.gov.cn/datadevelop/prod-api/open-portal/catalog/'

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('官网服务重定向')
    try:
        d = r.json()
    except ValueError as exc:
        raise RuntimeError('官网服务返回非 JSON') from exc
    if not isinstance(d, dict) or d.get('code') != 200 or 'data' not in d:
        raise RuntimeError('官网服务未成功返回数据')
    return d['data']

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9/-]{1,100}', value):
        raise ValueError('目录 ID 格式无效')
    return value

def search(keyword='', page=1, size=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or isinstance(size, bool) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('页码或每页条数无效')
    params = {'pageNum': page, 'pageSize': size, 'type': 1, 'deptCode': '', 'cityCode': '', 'format': '', 'openType': '', 'updateCycle': '', 'key': keyword, 'orderByColumn': '', 'isAsc': '', 'currentTab': 'all'}
    d = _get('list', params)
    if not isinstance(d, dict) or not isinstance(d.get('rows'), list) or (not isinstance(d.get('total'), int)) or isinstance(d.get('total'), bool) or (d['total'] < 0) or (len(d['rows']) > size) or (not d['rows'] and (page - 1) * size < d['total']):
        raise RuntimeError('官网目录分页或总数异常')
    fields = ('catalogID', 'catalogName', 'catalogDes', 'orgName', 'themeName', 'dataVol', 'updateTime', 'openType')
    return {'source': '福建省公共数据资源统一开放平台', 'keyword': keyword, 'page': page, 'size': size, 'total': d['total'], 'items': [{k: x.get(k) for k in fields} for x in d['rows']], 'note': '目录同时包含普遍开放及依申请开放；本次样本中 openType=1 对应普遍开放，实际预览前须核详情。目录条数不等于已获取数据。'}

def preview(catalog_id):
    _id(catalog_id)
    params = {'cataId': catalog_id}
    info = _get('getCataInfo', params)
    if not isinstance(info, dict) or info.get('catalogID') != catalog_id or info.get('openType') != '1':
        raise ValueError('仅支持已核验为普遍开放的数据目录')
    fields = _get('getCataItem', params)
    data = _get('getCataItemData', {'cataId': catalog_id, 'searchKey': '', 'searchKeyColumnId': ''})
    if not isinstance(fields, list) or not isinstance(data, dict) or (not isinstance(data.get('rows'), list)) or (not isinstance(data.get('total'), int)):
        raise RuntimeError('官网预览结构异常')
    if len(data['rows']) > 30:
        raise RuntimeError('官网预览超过已验证的30行范围')
    return {'source': '福建省公共数据资源统一开放平台', 'catalog_id': catalog_id, 'title': info.get('catalogName'), 'provider': info.get('orgName'), 'openType': info.get('openType'), 'updateTime': info.get('updateTime'), 'fields': fields, 'total': data['total'], 'rows': data['rows'], 'note': '官网只展示前30条样本，total 是上游总数，不等于预览行数；原值和单位须结合字段及数据说明核验。不同字段的数据更新时间可能早于目录更新时间。'}
