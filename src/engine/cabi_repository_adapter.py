"""CABI 开放数据仓库的 CKAN 官方接口，不是学校订购的 CABI 电子书。"""
import release_runtime
import re
import requests
BASE = 'https://datarepository.cabi.org'

def _get(action, params):
    r = requests.get(f'{BASE}/api/3/action/{action}', params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get('success') is not True or not isinstance(data.get('result'), dict):
        raise RuntimeError('CABI 仓库未返回有效结果')
    return data['result']

def _record(row):
    return {'id': row.get('id'), 'name': row.get('name'), 'title': row.get('title'), 'author': row.get('author'), 'license_title': row.get('license_title'), 'license_url': row.get('license_url'), 'metadata_modified': row.get('metadata_modified'), 'url': f"{BASE}/dataset/{row.get('name')}", 'resources': [{'name': v.get('name'), 'format': v.get('format'), 'url': v.get('url')} for v in row.get('resources', [])]}

def search_datasets(keyword='', start=0, rows=10):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('keyword 必须是不超过 200 字的字符串')
    if isinstance(start, bool) or not isinstance(start, int) or start < 0:
        raise ValueError('start 必须为非负整数')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 50):
        raise ValueError('rows 必须为 1 至 50 的整数')
    data = _get('package_search', {'q': keyword or '*:*', 'start': start, 'rows': rows})
    return {'source': 'CABI Data Repository 官方 CKAN API', 'keyword': keyword, 'total': data['count'], 'start': start, 'items': [_record(v) for v in data.get('results', [])], 'scope': '公开数据仓库，并非馆藏 CABI 电子书或 CAB Abstracts；每条数据许可须单独核对'}

def dataset_detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_-]{1,200}', identifier):
        raise ValueError('数据集编号或名称格式无效')
    data = _get('package_show', {'id': identifier})
    out = _record(data)
    out['description'] = data.get('notes')
    return out
