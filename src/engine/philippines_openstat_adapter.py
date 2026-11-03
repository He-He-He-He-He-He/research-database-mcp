"""菲律宾统计局 OpenSTAT PxWeb 主题、表结构及有界 CSV 数据查询。"""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
BASE = 'https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB'
MAX_BYTES = 10000000

def _path(path, table=False):
    if not isinstance(path, str) or len(path) > 250 or path.startswith('/') or ('..' in path) or (path and (not re.fullmatch('[A-Za-z0-9_./-]+', path))):
        raise ValueError('无效统计库路径')
    if table and (not path.endswith('.px')):
        raise ValueError('表路径须以 .px 结尾')
    return BASE + ('/' + path if path else '')

def _get(url, body=None):
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES)]
    if body is not None:
        args += ['-H', 'Content-Type: application/json', '--data-binary', '@-']
    p = release_runtime.run(args + [url], input=json.dumps(body).encode() if body is not None else None, capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('菲律宾 OpenSTAT 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return p.stdout.decode('utf-8-sig')

def browse(path=''):
    url = _path(path)
    value = json.loads(_get(url))
    if not isinstance(value, list):
        raise ValueError('目录响应异常')
    return {'source': url, 'items': value, 'note': '读取当前目录层级；未证明全部子目录或所有表可用。'}

def metadata(path):
    url = _path(path, True)
    value = json.loads(_get(url))
    if not isinstance(value, dict) or not isinstance(value.get('variables'), list):
        raise ValueError('元数据格式异常')
    return {'source': url, 'metadata': value, 'page_url': 'https://openstat.psa.gov.ph/PXWeb/pxweb/en/DB/DB__' + path.replace('/', '__', path.count('/') - 1), 'note': 'API 元数据可能不含单位、脚注和口径，请查原站对应表页。'}

def data(path, selections):
    m = metadata(path)['metadata']
    variables = m['variables']
    codes = [v['code'] for v in variables]
    if not isinstance(selections, dict) or set(selections) != set(codes):
        raise ValueError('必须显式指定每个变量：' + ', '.join(codes))
    query = []
    count = 1
    for v in variables:
        code = v['code']
        values = selections[code]
        if not isinstance(v.get('values'), list):
            raise ValueError('上游未提供变量 ' + code + ' 的取值代码，暂不能安全验证查询')
        if not isinstance(values, list) or not values or len(values) > 100 or any((not isinstance(x, str) or x not in v['values'] for x in values)) or (len(values) != len(set(values))):
            raise ValueError('变量 ' + code + ' 的值无效，请核对元数据')
        count *= len(values)
        if count > 5000:
            raise ValueError('单次最多 5000 个统计单元')
        query.append({'code': code, 'selection': {'filter': 'item', 'values': values}})
    url = _path(path, True)
    raw = _get(url, {'query': query, 'response': {'format': 'csv'}})
    rows = list(csv.reader(io.StringIO(raw, newline='')))
    if len(rows) < 2 or not rows[0]:
        raise ValueError('未识别 CSV 表格')
    return {'source': url, 'table_title': m.get('title'), 'requested_cells': count, 'selections': selections, 'csv_rows': rows, 'note': '原始 CSV 每行保留字符串；必须核对原表网页单位、注释与统计口径。当地上游示例 JSON-stat2 和 CSV 数值出现不一致，本适配器只返回 CSV。'}

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
