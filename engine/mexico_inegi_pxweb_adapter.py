"""墨西哥国家统计与地理研究所 INEGI PxWeb 表库。"""
import release_runtime
import argparse
import json
import re
import requests
from urllib.parse import quote
BASE = 'https://www.inegi.org.mx/app/tabulados/pxwebv2/api/v1/es'
MAX_BYTES = 10000000

def _path(path, table=False):
    if not isinstance(path, str) or len(path) > 500 or path.startswith('/') or ('..' in path):
        raise ValueError('无效路径')
    parts = path.split('/') if path else []
    if any((not x or not re.fullmatch('[\\w ,.()&-]+', x) for x in parts)):
        raise ValueError('路径含不允许的字符')
    if table and (not parts or not parts[-1].endswith('.px')):
        raise ValueError('表路径须以 .px 结尾')
    return BASE + ('' if not parts else '/' + '/'.join((quote(x, safe='') for x in parts)))

def _get(url, body=None):
    with requests.request('POST' if body is not None else 'GET', url, json=body, timeout=35, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > MAX_BYTES:
                raise ValueError('响应过大')
    return json.loads(raw)

def browse(path=''):
    url = _path(path)
    value = _get(url)
    if not isinstance(value, list):
        raise ValueError('目录响应异常')
    return {'source': url, 'items': value, 'note': 'INEGI 国家统计表库；指定目录当前层级不代表所有表均已验证。'}

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
    value = _get(url, {'query': query, 'response': {'format': 'json'}})
    if not isinstance(value, dict) or not isinstance(value.get('columns'), list) or (not isinstance(value.get('data'), list)):
        raise ValueError('数据响应异常')
    return {'source': url, 'selections': selections, 'requested_cells': cells, 'dataset': value, 'note': '保留 JSON 原始列、维度代码和字符串值；官方 JSON-stat2 在样例中返回错误值，故禁用。普查年度、样本调查与不同人口及住房口径不可混同。数据可能修订，观测年份不能证明历史可得性。'}

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
