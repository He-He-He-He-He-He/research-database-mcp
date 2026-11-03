"""浙江省公共数据开放平台目录搜索和无条件开放数据预览。"""
import release_runtime
import re
from urllib.parse import quote
import requests
BASE = 'https://data.zjzwfw.gov.cn/dopServer/dataCatalog/'

def _request(path, body):
    response = requests.post(BASE + path, json=body, timeout=30, allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect:
        raise RuntimeError('官方服务重定向，无法验证来源')
    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError('官方服务返回非 JSON') from exc
    if not isinstance(result, dict) or result.get('success') is not True or result.get('code') != '2000':
        raise RuntimeError('官方服务未成功返回数据')
    return result.get('result')

def search(keyword='', page=1, size=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 50):
        raise ValueError('每页1至50项')
    data = _request('categoryQueryPage', {'current': page, 'size': size, 'dataName': keyword})
    if not isinstance(data, dict) or not isinstance(data.get('records'), list) or data.get('current') != page or (data.get('size') != size):
        raise RuntimeError('目录响应结构或分页异常')
    total = data.get('total')
    if isinstance(total, bool) or not isinstance(total, int) or total < 0 or (len(data['records']) > size) or (not data['records'] and (page - 1) * size < total):
        raise RuntimeError('目录总数与结果不一致')
    fields = ('id', 'sourceCode', 'sourceName', 'openType', 'privateDept', 'regionName', 'updateTime', 'dataTimeRange', 'description')
    return {'source': '浙江省公共数据开放平台', 'keyword': keyword, 'page': page, 'size': size, 'total': total, 'items': [{k: x.get(k) for k in fields} for x in data['records']], 'note': '目录含无条件及受限开放项目；A 为样本中无条件开放，获取数据前须检查具体项目权限与条款。目录数不等于可下载或已验证数量。'}

def preview(resource_id):
    if not isinstance(resource_id, str) or not re.fullmatch('[A-Za-z0-9+/=]{8,128}', resource_id):
        raise ValueError('请提供目录返回的资源 ID')
    encoded = quote(resource_id, safe='')
    detail = _request('catalogDetail/' + encoded, {})
    if not isinstance(detail, dict) or not isinstance(detail.get('dopSourceInfo'), dict):
        raise RuntimeError('无法核验开放属性')
    meta = detail['dopSourceInfo']
    if meta.get('id') != resource_id or meta.get('openType') != 'A':
        raise ValueError('仅支持已核验为无条件开放的资源预览')
    result = _request('catalogDataPreview/' + encoded, {})
    if not isinstance(result, dict) or not isinstance(result.get('sourceInfo'), dict) or (not isinstance(result.get('data'), list)):
        raise RuntimeError('预览结构异常')
    info = result['sourceInfo']
    rows = result['data']
    if info.get('id') != resource_id or info.get('openType') != 'A' or (not rows) or (not all((isinstance(row, list) for row in rows))):
        raise RuntimeError('预览身份、开放属性或表格结构异常')
    return {'source': '浙江省公共数据开放平台', 'id': resource_id, 'metadata': {k: info.get(k) for k in ('sourceName', 'sourceCode', 'openType', 'privateDept', 'updateTime', 'updateCycleDetail', 'dataTimeRange')}, 'header': rows[0], 'rows': rows[1:], 'note': '官网预览样本，不是全量数据；空值、单位、更新时间及数据口径以原始字段和来源说明为准。'}
