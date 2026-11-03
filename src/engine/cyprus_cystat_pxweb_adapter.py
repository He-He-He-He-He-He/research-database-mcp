"""塞浦路斯统计局 CYSTAT PxWeb 目录、元数据及 CSV 查询。"""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
from urllib.parse import quote
BASE = 'https://cystatdb.cystat.gov.cy/api/v1/en/8.CYSTAT-DB'
MAX_BYTES = 10000000

def _path(path, table=False):
    if not isinstance(path, str) or len(path) > 500 or path.startswith('/') or ('..' in path):
        raise ValueError('无效路径')
    parts = path.split('/') if path else []
    if any((not x or not re.fullmatch('[\\w ,.()-]+', x) for x in parts)):
        raise ValueError('路径含不允许的字符')
    if table and (not parts or not parts[-1].endswith('.px')):
        raise ValueError('表路径须以 .px 结尾')
    return BASE + ('' if not parts else '/' + '/'.join((quote(x, safe='') for x in parts))) + ('/' if table else '')

def _get(url, body=None):
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES)]
    if body is not None:
        args += ['-H', 'Content-Type: application/json', '--data-binary', '@-']
    p = release_runtime.run(args + [url], input=json.dumps(body, ensure_ascii=False).encode() if body is not None else None, capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('CYSTAT 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return p.stdout

def browse(path=''):
    url = _path(path)
    value = json.loads(_get(url))
    if not isinstance(value, list):
        raise ValueError('目录响应异常')
    return {'source': url, 'items': value, 'note': '返回指定目录当前层级；不代表所有子库及表均已验。'}

def metadata(path):
    url = _path(path, True)
    value = json.loads(_get(url))
    if not isinstance(value, dict) or not isinstance(value.get('variables'), list):
        raise ValueError('表结构响应异常')
    return {'source': url, 'metadata': value, 'note': 'API 元数据可能未含单位、脚注、统计方法；须核对原站发布及表说明。'}

def data(path, selections):
    info = metadata(path)['metadata']
    variables = info['variables']
    codes = [v['code'] for v in variables]
    if not isinstance(selections, dict) or set(selections) != set(codes):
        raise ValueError('须显式指定所有变量：' + ', '.join(codes))
    query = []
    cells = 1
    for v in variables:
        code = v['code']
        vals = selections[code]
        if not isinstance(v.get('values'), list):
            raise ValueError('上游未提供变量取值：' + code)
        if not isinstance(vals, list) or not vals or len(vals) > 100 or any((not isinstance(x, str) or x not in v['values'] for x in vals)) or (len(vals) != len(set(vals))):
            raise ValueError('变量 ' + code + ' 取值无效')
        cells *= len(vals)
        if cells > 5000:
            raise ValueError('单次最多 5000 个统计单元')
        query.append({'code': code, 'selection': {'filter': 'item', 'values': vals}})
    url = _path(path, True)
    raw = _get(url, {'query': query, 'response': {'format': 'csv'}})
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    rows = list(csv.reader(io.StringIO(text, newline='')))
    if len(rows) < 2:
        raise ValueError('未识别 CSV 数据')
    return {'source': url, 'table_title': info.get('title'), 'selections': selections, 'requested_cells': cells, 'csv_rows': rows, 'note': '保留 CSV 原始字符串、空值和特殊符号；数据单位和统计边界必须核对原始表说明。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('browse')
    q.add_argument('path', nargs='?', default='')
    q = s.add_parser('metadata')
    q.add_argument('path')
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('--selections', required=True)
    a = p.parse_args()
    v = browse(a.path) if a.cmd == 'browse' else metadata(a.path) if a.cmd == 'metadata' else data(a.path, json.loads(a.selections))
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
