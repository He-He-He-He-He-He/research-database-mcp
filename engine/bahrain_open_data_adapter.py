"""巴林官方开放数据目录及数据记录 API。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.gov.bh/api/explore/v2.1/catalog/datasets'
MAX_BYTES = 10000000

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('巴林开放数据请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return (url, json.loads(p.stdout))

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('[a-z0-9][a-z0-9_-]{0,199}', value):
        raise ValueError('数据集 ID 无效')
    return value

def search(keyword, limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or any((c in keyword for c in ('"', '\\', '\n', '\r'))):
        raise ValueError('关键词无效')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('分页无效')
    url, data = _get('', {'where': 'search("' + keyword.strip() + '")', 'limit': limit, 'offset': offset})
    if not isinstance(data, dict) or not isinstance(data.get('results'), list):
        raise ValueError('目录响应异常')
    return {'source': url, 'data': data, 'note': '门户包含多机构开放数据；请核对每个数据集发布机构、许可、时间和统计范围。'}

def metadata(dataset):
    url, data = _get('/' + _id(dataset))
    if not isinstance(data, dict) or data.get('dataset_id') != dataset:
        raise ValueError('元数据响应异常')
    return {'source': url, 'metadata': data, 'note': '包含字段、来源、单位说明及许可等信息；具体可用性以返回内容及原始说明为准。'}

def records(dataset, filters=None, fields=None, limit=20, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('分页无效')
    meta = metadata(dataset)['metadata']
    field_info = {x.get('name'): x for x in meta.get('fields', []) if isinstance(x, dict)}
    columns = set(field_info)
    params = {'limit': limit, 'offset': offset}
    if fields:
        if not isinstance(fields, list) or len(fields) > 30 or any((not isinstance(x, str) or x not in columns or (not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,100}', x)) for x in fields)):
            raise ValueError('查询字段不在元数据中')
        params['select'] = ','.join(fields)
    if filters:
        if not isinstance(filters, dict) or len(filters) > 8:
            raise ValueError('过滤条件无效')
        expressions = []
        for k, v in filters.items():
            if not isinstance(k, str) or k not in columns or (not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,100}', k)) or (not isinstance(v, str)) or (not v) or (len(v) > 150) or any((c in v for c in ('"', '\\', '\n', '\r'))):
                raise ValueError('过滤字段或值无效')
            if field_info[k].get('type') != 'text':
                raise ValueError('目前仅支持 text 类型的精确筛选；日期或数值字段请先查看元数据')
            expressions.append(k + '="' + v + '"')
        params['where'] = ' AND '.join(expressions)
    url, data = _get('/' + _id(dataset) + '/records', params)
    if not isinstance(data, dict) or not isinstance(data.get('results'), list):
        raise ValueError('记录响应异常')
    return {'source': url, 'dataset': dataset, 'data': data, 'note': '数据由各发布机构提供；保留原始数值、年份和字段。分页 total_count 是查询匹配数；字段、单位、许可及统计口径应以元数据为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--offset', type=int, default=0)
    q = s.add_parser('metadata')
    q.add_argument('dataset')
    q = s.add_parser('records')
    q.add_argument('dataset')
    q.add_argument('--filters', default='{}')
    q.add_argument('--fields', default='')
    q.add_argument('--limit', type=int, default=20)
    q.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    v = search(a.keyword, a.limit, a.offset) if a.cmd == 'search' else metadata(a.dataset) if a.cmd == 'metadata' else records(a.dataset, json.loads(a.filters), a.fields.split(',') if a.fields else None, a.limit, a.offset)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
