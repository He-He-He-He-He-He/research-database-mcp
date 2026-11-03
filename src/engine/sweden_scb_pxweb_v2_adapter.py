"""瑞典统计数据库 PxWeb API v2：检索、元数据与有界统计查询。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://statistikdatabasen.scb.se/api/v2'
MAX_BYTES = 12000000

def _get(path, params=None, body=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES)]
    if body is not None:
        args += ['--header', 'Content-Type: application/json', '--data-binary', '@-']
    r = release_runtime.run(args + [url], input=json.dumps(body).encode() if body is not None else None, capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('SCB 请求失败：' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小限制')
    return (url, json.loads(r.stdout))

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('TAB[0-9]{1,10}', value):
        raise ValueError('无效表编号')
    return value

def search(keyword, page=1, page_size=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000) or isinstance(page_size, bool) or (not isinstance(page_size, int)) or (not 1 <= page_size <= 100):
        raise ValueError('无效分页')
    url, result = _get('/tables', {'lang': 'en', 'query': keyword.strip(), 'pageNumber': page, 'pageSize': page_size})
    if not isinstance(result, dict) or not isinstance(result.get('tables'), list):
        raise ValueError('上游目录格式异常')
    return {'source': url, 'data': result, 'note': '表的 source 可能为瑞典统计局或其他统计机构，引用应遵循对应来源。'}

def metadata(table):
    url, result = _get('/tables/' + _id(table) + '/metadata', {'lang': 'en'})
    if result.get('class') != 'dataset' or not isinstance(result.get('dimension'), dict):
        raise ValueError('元数据格式异常')
    return {'source': url, 'metadata': result, 'note': '保留所有维度、说明、单位、状态以及来源；目录和表会随上游变更。'}

def data(table, selections):
    info = metadata(table)['metadata']
    ids = info['id']
    dims = info['dimension']
    if not isinstance(selections, dict) or set(selections) != set(ids):
        raise ValueError('须显式指定所有维度：' + ', '.join(ids))
    query = []
    cells = 1
    for code in ids:
        vals = selections[code]
        allowed = dims[code]['category']['index']
        if not isinstance(vals, list) or not vals or len(vals) > 100 or any((not isinstance(x, str) or x not in allowed for x in vals)) or (len(vals) != len(set(vals))):
            raise ValueError('维度 ' + code + ' 的值无效，请查看元数据')
        cells *= len(vals)
        if cells > 5000:
            raise ValueError('本工具单次最多 5000 个统计单元')
        query.append({'variableCode': code, 'valueCodes': vals})
    url, result = _get('/tables/' + _id(table) + '/data', {'lang': 'en', 'outputFormat': 'json-stat2'}, {'selection': query})
    if result.get('class') != 'dataset' or 'value' not in result:
        raise ValueError('未识别 JSON-stat2 数据')
    return {'source': url, 'requested_cells': cells, 'selections': selections, 'dataset': result, 'note': '保留官方 JSON-stat2 维度、索引、单位、来源和状态；缺失值不代表零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--page-size', type=int, default=20)
    q = s.add_parser('metadata')
    q.add_argument('table')
    q = s.add_parser('data')
    q.add_argument('table')
    q.add_argument('--selections', required=True)
    a = p.parse_args()
    result = search(a.keyword, a.page, a.page_size) if a.cmd == 'search' else metadata(a.table) if a.cmd == 'metadata' else data(a.table, json.loads(a.selections))
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
