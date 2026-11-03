"""克罗地亚统计局 DZS 公开 PxWeb 目录、元数据和统计数据。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import quote
BASE = 'https://web.dzs.hr/PxWeb/api/v1/en'
MAX_BYTES = 10000000

def _path(path, table=False):
    if not isinstance(path, str) or len(path) > 500 or path.startswith('/') or ('..' in path):
        raise ValueError('无效路径')
    parts = path.split('/') if path else []
    if any((not x or not re.fullmatch('[\\w ,.()&–-]+', x) for x in parts)):
        raise ValueError('路径含不允许的字符')
    if table and (not parts or not parts[-1].endswith('.px')):
        raise ValueError('表路径须以 .px 结尾')
    return BASE + ('' if not parts else '/' + '/'.join((quote(x, safe='') for x in parts)))

def _get(url, body=None):
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES)]
    if body is not None:
        args += ['-H', 'Content-Type: application/json', '--data-binary', '@-']
    p = release_runtime.run(args + [url], input=json.dumps(body, ensure_ascii=False).encode() if body is not None else None, capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('克罗地亚统计 API 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return json.loads(p.stdout)

def browse(path=''):
    url = _path(path)
    value = _get(url)
    if not isinstance(value, list):
        raise ValueError('目录响应异常')
    return {'source': url, 'items': value, 'note': '返回指定目录当前层级；不代表所有子库和统计表均已验证。'}

def metadata(path):
    url = _path(path, True)
    value = _get(url)
    if not isinstance(value, dict) or not isinstance(value.get('variables'), list):
        raise ValueError('表结构响应异常')
    return {'source': url, 'metadata': value, 'note': '读取可选维度、代码及标签；单位、基期和方法以官方页面与注释为准。'}

def data(path, selections):
    meta = metadata(path)['metadata']
    variables = meta['variables']
    codes = [v['code'] for v in variables]
    if not isinstance(selections, dict) or set(selections) != set(codes):
        raise ValueError('须显式指定全部变量：' + ', '.join(codes))
    query = []
    cells = 1
    for v in variables:
        code = v['code']
        vals = selections[code]
        if not isinstance(v.get('values'), list):
            raise ValueError('上游未提供取值代码：' + code)
        if not isinstance(vals, list) or not vals or len(vals) > 100 or any((not isinstance(x, str) or x not in v['values'] for x in vals)) or (len(vals) != len(set(vals))):
            raise ValueError('变量 ' + code + ' 取值无效')
        cells *= len(vals)
        if cells > 5000:
            raise ValueError('单次最多 5000 个单元')
        query.append({'code': code, 'selection': {'filter': 'item', 'values': vals}})
    url = _path(path, True)
    value = _get(url, {'query': query, 'response': {'format': 'json-stat2'}})
    if not isinstance(value, dict) or value.get('class') != 'dataset' or 'value' not in value:
        raise ValueError('数据响应异常')
    return {'source': url, 'selections': selections, 'requested_cells': cells, 'dataset': value, 'note': '保留 JSON-stat2 原始维度、值、单位、注释及状态；缺失不为零，时间和定义须核对官方表。'}

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
