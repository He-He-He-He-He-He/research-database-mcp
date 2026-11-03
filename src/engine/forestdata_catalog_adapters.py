"""国家林业和草原科学数据中心公开目录单页筛选及元数据。"""
import release_runtime
import re
import requests
BASE = 'https://www.forestdata.cn/api/portal/data/'
FIELDS = ('id', 'name', 'nameEn', 'doi', 'cstr', 'keywords', 'description', 'resourceType', 'dataFormat', 'province', 'city', 'subject', 'dataTime', 'dataCreateTime', 'approveTime', 'shareType', 'shareTypeZh', 'publisherName', 'dataQuality')

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if x.get('code') != 200:
        raise ValueError('上游未返回成功')
    return x

def forestdata_catalog(keyword='', page=1, size=10):
    if not isinstance(keyword, str) or len(keyword) > 100 or (not isinstance(page, int)) or (not 1 <= page <= 100) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('请检查关键词与分页')
    x = _get('list', {'pageNum': page, 'pageSize': size})
    rows = x.get('rows')
    if not isinstance(rows, list):
        raise ValueError('未识别目录')
    items = [{k: v for k, v in a.items() if k in FIELDS} for a in rows if keyword.lower() in str(a.get('name', '')).lower()]
    return {'page': page, 'upstream_total': x.get('total'), 'items': items, 'note': '只在上游当前页名称本地筛选，total 是目录总数，不是关键词命中总数。'}

def forestdata_detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[a-f0-9]{32}', identifier):
        raise ValueError('请输入数据集编号')
    x = _get(identifier).get('data')
    if not isinstance(x, dict) or x.get('id') != identifier:
        raise ValueError('未识别数据集')
    return {k: v for k, v in x.items() if k in FIELDS}
