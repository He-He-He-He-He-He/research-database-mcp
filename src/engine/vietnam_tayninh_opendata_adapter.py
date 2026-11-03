"""越南西宁省开放数据平台 CKAN 目录与 DataStore 分页查询。"""
import release_runtime
import argparse
import json
import math
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.tayninh.gov.vn/api/3/action/'
MAX_BYTES = 10000000

def _get(action, params):
    if action not in ('package_search', 'package_show', 'datastore_search'):
        raise ValueError('无效操作')
    url = BASE + action + '?' + urlencode(params)
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('越南西宁省数据平台请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    value = json.loads(p.stdout)
    if not isinstance(value, dict) or value.get('success') is not True or (not isinstance(value.get('result'), dict)):
        raise ValueError('上游返回错误')
    return (url, value['result'])

def search(keyword, limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('分页无效')
    url, data = _get('package_search', {'q': keyword, 'rows': limit, 'start': offset})
    if not isinstance(data.get('results'), list):
        raise ValueError('目录结构异常')
    return {'source': url, 'result': data, 'note': '门户包含不同部门和其他机构数据；须核对机构、年份、许可及来源。'}

def metadata(dataset):
    if not isinstance(dataset, str) or not re.fullmatch('[a-z0-9][a-z0-9_-]{0,180}', dataset):
        raise ValueError('数据集名称无效')
    url, value = _get('package_show', {'id': dataset})
    if value.get('name') != dataset:
        raise ValueError('数据集名称不匹配')
    return {'source': url, 'metadata': value, 'note': '请检查资源是否 datastore_active、数据时间范围、单位、发布者与许可。'}

def _resource(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value):
        raise ValueError('资源 UUID 无效')
    return value

def fields(resource):
    url, value = _get('datastore_search', {'resource_id': _resource(resource), 'limit': 0})
    if not isinstance(value.get('fields'), list):
        raise ValueError('DataStore 字段响应异常')
    return {'source': url, 'fields': value['fields'], 'total': value.get('total'), 'note': '数据存储字段类型不代替数据集的统计单位与方法说明。'}

def records(resource, filters=None, limit=20, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('分页无效')
    available = {x['id'] for x in fields(resource)['fields']}
    params = {'resource_id': _resource(resource), 'limit': limit, 'offset': offset}
    if filters:
        if not isinstance(filters, dict) or len(filters) > 8:
            raise ValueError('筛选条件无效')
        for k, v in filters.items():
            if not isinstance(k, str) or k not in available or isinstance(v, bool) or (not isinstance(v, (str, int, float))) or (isinstance(v, float) and (not math.isfinite(v))) or (isinstance(v, str) and len(v) > 150):
                raise ValueError('筛选字段或值无效')
        params['filters'] = json.dumps(filters, ensure_ascii=False, separators=(',', ':'))
    url, value = _get('datastore_search', params)
    if not isinstance(value.get('records'), list):
        raise ValueError('DataStore 数据结构异常')
    return {'source': url, 'result': value, 'note': '返回上游当前页和记录总数；各资源来自不同发布者，须结合数据集元数据核对年份、单位、许可和范围。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--offset', type=int, default=0)
    q = s.add_parser('metadata')
    q.add_argument('dataset')
    q = s.add_parser('fields')
    q.add_argument('resource')
    q = s.add_parser('records')
    q.add_argument('resource')
    q.add_argument('--filters', default='{}')
    q.add_argument('--limit', type=int, default=20)
    q.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    v = search(a.keyword, a.limit, a.offset) if a.cmd == 'search' else metadata(a.dataset) if a.cmd == 'metadata' else fields(a.resource) if a.cmd == 'fields' else records(a.resource, json.loads(a.filters), a.limit, a.offset)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
