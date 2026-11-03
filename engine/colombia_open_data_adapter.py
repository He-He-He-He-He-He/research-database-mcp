"""哥伦比亚政府开放数据目录、元数据和公开数据集 SODA 读取。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
CAT = 'https://api.us.socrata.com/api/catalog/v1'
HOST = 'https://www.datos.gov.co'
MAX_BYTES = 8000000

def _get(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('哥伦比亚开放数据请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    return json.loads(p.stdout)

def _id(ident):
    if not isinstance(ident, str) or not re.fullmatch('[a-z0-9]{4}-[a-z0-9]{4}', ident):
        raise ValueError('数据集 ID 无效')
    return ident

def search(keyword, limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入检索词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('分页参数无效')
    url = CAT + '?' + urlencode({'domains': 'datos.gov.co', 'q': keyword, 'only': 'datasets', 'limit': limit, 'offset': offset})
    data = _get(url)
    if not isinstance(data, dict) or not isinstance(data.get('results'), list):
        raise ValueError('目录响应异常')
    return {'source': url, 'result': data, 'note': '哥伦比亚政府开放平台汇集多级机构和转载数据，不等于均由 DANE 制作；应核对每项发布者、原始来源及许可。'}

def metadata(ident):
    url = HOST + '/api/views/' + _id(ident) + '.json'
    data = _get(url)
    if not isinstance(data, dict) or data.get('id') != ident:
        raise ValueError('元数据响应异常')
    return {'source': url, 'metadata': data, 'note': '须核对 attribution、description、columns 和许可。某些目录项是外链，不能用 SODA 数据查询。'}

def records(ident, filters=None, limit=20, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('分页参数无效')
    m = metadata(ident)['metadata']
    columns = {x.get('fieldName') for x in m.get('columns', []) if isinstance(x, dict)}
    if m.get('assetType') not in ('dataset', 'view'):
        raise ValueError('该目录项未标记为可读取的表；请查看元数据')
    params = {'$limit': limit, '$offset': offset}
    if filters:
        if not isinstance(filters, dict) or len(filters) > 8:
            raise ValueError('筛选条件格式无效')
        for key, value in filters.items():
            if not isinstance(key, str) or key not in columns or (not re.fullmatch('[a-zA-Z0-9_]{1,100}', key)) or (not isinstance(value, str)) or (not value) or (len(value) > 200):
                raise ValueError('无效字段或筛选值')
            params[key] = value
    url = HOST + '/resource/' + _id(ident) + '.json?' + urlencode(params)
    data = _get(url)
    if not isinstance(data, list):
        raise ValueError('数据响应异常')
    return {'source': url, 'dataset': ident, 'attribution': m.get('attribution'), 'name': m.get('name'), 'records': data, 'returned': len(data), 'limit': limit, 'offset': offset, 'note': '只读公开记录，不保证 API 支持所有资产；达到 limit 可能有更多记录。注意数据发布者、统计时间、缺失和数据许可。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--offset', type=int, default=0)
    q = s.add_parser('metadata')
    q.add_argument('id')
    q = s.add_parser('records')
    q.add_argument('id')
    q.add_argument('--filters', default='{}')
    q.add_argument('--limit', type=int, default=20)
    q.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    x = search(a.keyword, a.limit, a.offset) if a.cmd == 'search' else metadata(a.id) if a.cmd == 'metadata' else records(a.id, json.loads(a.filters), a.limit, a.offset)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
