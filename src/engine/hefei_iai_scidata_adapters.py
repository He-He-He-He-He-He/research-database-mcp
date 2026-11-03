"""合肥综合性国家科学中心人工智能研究院科学数据公开元数据。"""
import release_runtime
import re
import requests
BASE = 'https://iai.ustc.edu.cn/opendata/mids/api/'
FIELDS = ('id', 'name', 'category', 'permission', 'permissionDesc', 'intro', 'collectDate', 'updateDate', 'createDate', 'team', 'tags', 'detailAvailable')
VERSION_FIELDS = ('version', 'detailDesc', 'intro', 'omicsGroupStr', 'dataType', 'dataFormat', 'collectMethod', 'collectStartTime', 'collectEndTime', 'size', 'fileCount', 'sampleCount', 'createDate', 'collectDate', 'updateDate')

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if x.get('code') != 0 or not isinstance(x.get('data'), dict):
        raise ValueError('上游未返回公开数据')
    return x['data']

def iai_datasets(keyword, page=1, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(page, int)) or (not 1 <= page <= 100) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('请检查关键词及分页')
    x = _get('v2/dataset/list', {'query': keyword, 'page_no': page, 'page_size': size})
    rows = x.get('data')
    if not isinstance(rows, list):
        raise ValueError('未识别目录')
    return {'total': x.get('total'), 'page': x.get('pageNo'), 'items': [{k: v for k, v in row.items() if k in FIELDS} for row in rows]}

def iai_dataset_detail(identifier):
    if not re.fullmatch('\\d{1,30}', str(identifier)):
        raise ValueError('请输入数据集编号')
    x = _get('v3/dataset/detail', {'dataset_id': str(identifier)})
    if str(x.get('id')) != str(identifier):
        raise ValueError('上游数据集编号不匹配')
    fields = ('id', 'name', 'team', 'category', 'domain', 'permission', 'permissionDesc', 'tags', 'size', 'createDate', 'serialNumber', 'terms')
    out = {k: v for k, v in x.items() if k in fields}
    out['versions'] = [{k: v for k, v in version.items() if k in VERSION_FIELDS} for version in x.get('versions', []) if isinstance(version, dict)]
    return out
