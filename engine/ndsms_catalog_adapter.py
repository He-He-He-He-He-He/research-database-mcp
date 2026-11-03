"""国家数据集管理服务平台公开目录与元数据；不下载数据集。"""
import release_runtime
import re
import requests
BASE = 'https://www.ndsms.cn/api/cedc-dsm-backend-main/public'
FIELDS = ('id', 'datasetName', 'datasetDesc', 'supplierName', 'industryName', 'areaName', 'contentName', 'taskName', 'datasetKeyDomainName', 'size', 'sizeUnit', 'createdTime', 'updatedTime', 'hasPermission', 'openScope', 'limitation', 'authorize', 'dataLevel', 'frequency', 'metaDataList')

def _request(method, path, **kwargs):
    r = requests.request(method, BASE + path, timeout=25, allow_redirects=False, **kwargs)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 10000000:
        raise ValueError('响应重定向或过大')
    j = r.json()
    if not j.get('success') or j.get('code') != 200 or j.get('data') is None:
        raise ValueError('平台请求失败：' + str(j.get('message', ''))[:200])
    return j['data']

def catalog(page=1, size=10, keyword=''):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('page 应为 1–10000')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 20):
        raise ValueError('size 应为 1–20')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword 最多 100 字')
    d = _request('POST', '/navigate/datasetList', json={'pageIndex': page, 'pageSize': size})
    if d.get('pageIndex') != page or not isinstance(d.get('list'), list):
        raise ValueError('列表格式或页码异常')
    rows = []
    for row in d['list']:
        if keyword and keyword.casefold() not in (str(row.get('datasetName', '')) + ' ' + str(row.get('datasetDesc', ''))).casefold():
            continue
        rows.append({k: row.get(k) for k in FIELDS if k in row})
    return {'source': '国家数据集管理服务平台公开目录', 'page': page, 'page_size': size, 'reported_total': d.get('total'), 'keyword': keyword, 'items': rows, 'note': '关键词只筛选当前页，平台条目由数据提供方描述；列入目录不代表数据开放、免费、质量经独立核实或可下载。'}

def catalog_all(keyword='', limit=100, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword 最多 100 字')
    if type(limit) is not int or not 1 <= limit <= 500 or type(offset) is not int or (not 0 <= offset <= 100000):
        raise ValueError('limit 或 offset 无效')
    rows = []
    seen = set()
    expected = None
    pages = 0
    for page in range(1, 21):
        d = _request('POST', '/navigate/datasetList', json={'pageIndex': page, 'pageSize': 500})
        if not isinstance(d, dict) or d.get('pageIndex') != page or d.get('pageSize') != 500 or (type(d.get('total')) is not int) or (d['total'] < 0) or (not isinstance(d.get('list'), list)) or (len(d['list']) > 500):
            raise ValueError('目录页或大小异常')
        if expected is None:
            expected = d['total']
        if d['total'] != expected:
            raise ValueError('读取期间目录总数变化，请重试')
        for item in d['list']:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or (not re.fullmatch('[0-9a-fA-F]{32}', item['id'])) or (item['id'] in seen):
                raise ValueError('目录标识缺失或重复')
            seen.add(item['id'])
            rows.append(item)
        pages = page
        if len(rows) >= expected:
            break
        if not d['list']:
            raise ValueError('目录提前结束')
    else:
        raise ValueError('目录超过20页安全上限')
    if len(rows) != expected:
        raise ValueError('目录数量不一致')
    q = keyword.casefold()
    matched = [x for x in rows if q in (str(x.get('datasetName', '')) + ' ' + str(x.get('datasetDesc', ''))).casefold()]
    return {'source': '国家数据集管理服务平台公开目录', 'reported_total': expected, 'source_pages_fetched': pages, 'keyword': keyword, 'matched_total': len(matched), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(matched) else None, 'items': [{k: x.get(k) for k in FIELDS if k in x} for x in matched[offset:offset + limit]], 'note': '逐页获取目录、校验总数与标识后在本地筛选；源端无原子快照，更新时仍可能变化。目录由提供方描述，不代表数据开放、免费、质量经独立核实或可下载。'}

def detail(dataset_id):
    if not isinstance(dataset_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', dataset_id):
        raise ValueError('数据集 ID 须为 32 位十六进制')
    d = _request('GET', '/navigate/detail', params={'dataset_id': dataset_id})
    if d.get('id') != dataset_id:
        raise ValueError('返回标识不符')
    return {'source': '国家数据集管理服务平台', 'item': {k: d.get(k) for k in FIELDS if k in d}, 'note': '提供方描述和许可限制需自行核实；此接口仅读目录与元数据，不下载数据集，也不代表用户有权限。'}

def classifications(kind):
    paths = {'areas': '/area/all', 'industries': '/industry/all', 'tasks': '/task/all', 'content': '/contentClassify/all'}
    if kind not in paths:
        raise ValueError('分类仅支持 areas, industries, tasks, content')
    return {'source': '国家数据集管理服务平台分类', 'kind': kind, 'items': _request('GET', paths[kind]), 'note': '平台分类不代表数据开放或已有记录。'}
