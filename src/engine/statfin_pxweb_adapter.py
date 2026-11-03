"""芬兰统计局 StatFin PxWeb 目录、表结构与有界数据查询。"""
import release_runtime
import argparse
import json
import math
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin'
MAX_BYTES = 12000000

def _path(path, table=False):
    if not isinstance(path, str) or len(path) > 250 or path.startswith('/') or ('..' in path) or (path and (not re.fullmatch('[A-Za-z0-9_./-]+', path))):
        raise ValueError('无效 StatFin 路径')
    if table and (not path.endswith('.px')):
        raise ValueError('统计表路径必须以 .px 结尾')
    return BASE + ('/' + path if path else '')

def _get(url, body=None):
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(MAX_BYTES)]
    if body is not None:
        args += ['--header', 'Content-Type: application/json', '--data-binary', '@-']
    r = release_runtime.run(args + [url], input=json.dumps(body).encode() if body is not None else None, capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('StatFin 请求失败：' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('StatFin 响应过大')
    return json.loads(r.stdout)

def browse(path=''):
    url = _path(path)
    data = _get(url)
    if not isinstance(data, list):
        raise ValueError('上游返回的不是目录')
    return {'source': url, 'items': data, 'note': '目录包含统计主题和统计表；表代码与内容会随更新变化。'}

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    url = BASE + '?' + urlencode({'query': keyword.strip()})
    data = _get(url)
    if not isinstance(data, list):
        raise ValueError('上游返回的不是目录')
    return {'source': url, 'items': data, 'note': '上游关键词搜索；无结果不代表不存在。'}

def metadata(path):
    url = _path(path, True)
    data = _get(url)
    if not isinstance(data, dict) or not isinstance(data.get('variables'), list):
        raise ValueError('上游表结构不符合预期')
    return {'source': url, 'metadata': data, 'note': '读取全部变量代码与候选值；应核对统计口径及上游修订。'}

def data(path, selections):
    if not isinstance(selections, dict) or not selections:
        raise ValueError('需要变量代码与值数组')
    info = metadata(path)['metadata']
    variables = info['variables']
    codes = [v.get('code') for v in variables]
    if set(selections) != set(codes):
        raise ValueError('必须显式指定每个变量：' + ', '.join(codes))
    count = 1
    query = []
    for var in variables:
        code = var['code']
        vals = selections[code]
        if not isinstance(vals, list) or not vals or len(vals) > 100 or any((not isinstance(x, str) or x not in var['values'] for x in vals)) or (len(set(vals)) != len(vals)):
            raise ValueError('变量 ' + code + ' 的值无效，须从元数据选择')
        count *= len(vals)
        if count > 5000:
            raise ValueError('单次查询最多 5000 个统计单元')
        query.append({'code': code, 'selection': {'filter': 'item', 'values': vals}})
    url = _path(path, True)
    value = _get(url, {'query': query, 'response': {'format': 'json-stat2'}})
    if value.get('class') != 'dataset' or 'dimension' not in value or 'value' not in value:
        raise ValueError('上游未返回预期 JSON-stat 数据')
    return {'source': url, 'selections': selections, 'requested_cells': count, 'dataset': value, 'note': '保留 JSON-stat 维度顺序、单位、状态及元数据。数值顺序由 id、size 和 category.index 决定；缺失不等于零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('browse')
    q.add_argument('path', nargs='?', default='')
    q = s.add_parser('search')
    q.add_argument('keyword')
    q = s.add_parser('metadata')
    q.add_argument('path')
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('--selections', required=True, help='变量代码到选定代码数组的 JSON 对象')
    a = p.parse_args()
    value = browse(a.path) if a.cmd == 'browse' else search(a.keyword) if a.cmd == 'search' else metadata(a.path) if a.cmd == 'metadata' else data(a.path, json.loads(a.selections))
    print(json.dumps(value, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
