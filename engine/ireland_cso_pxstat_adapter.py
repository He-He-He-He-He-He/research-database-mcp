"""Ireland CSO PxStat table catalogue and JSON-stat2 datasets."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://ws.cso.ie/public/'

def _get(path, params=None, limit=12 * 1024 * 1024):
    with requests.get(BASE + path, params=params, timeout=55, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > limit:
                raise ValueError('response exceeds size limit')
            parts.append(b)
        result = json.loads(b''.join(parts))
        if result.get('error'):
            raise ValueError(str(result['error']))
        return (r.url, result)

def search(keyword, limit=20, datefrom='2000-01-01', *, offset=0):
    if not keyword or len(keyword) > 120 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000) or (not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', datefrom)):
        raise ValueError('invalid search')
    q = {'jsonrpc': '2.0', 'method': 'PxStat.Data.Cube_API.ReadCollection', 'params': {'language': 'en', 'datefrom': datefrom}}
    url, d = _get('api.jsonrpc', {'data': json.dumps(q, separators=(',', ':'))}, limit=32 * 1024 * 1024)
    items = d['result']['link']['item']
    matches = []
    for item in items:
        e = item.get('extension', {})
        matrix = e.get('matrix', '')
        label = item.get('label', '')
        if keyword.casefold() in (matrix + ' ' + label).casefold():
            matches.append({'id': matrix, 'label': label, 'updated': item.get('updated'), 'source': e.get('copyright')})
    return {'source': url, 'count': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(matches) else None, 'results': matches[offset:offset + limit], 'note': '按指定日期起的目录检索，不包含更早且未在该日期之后更新的表；每次完整获取目录并在本地截取，跨请求排序可能变化。'}

def dataset(table):
    if not re.fullmatch('[A-Za-z0-9]{2,15}', table):
        raise ValueError('invalid table id')
    url, d = _get('api.restful/PxStat.Data.Cube_API.ReadDataset/' + table.upper() + '/JSON-stat/2.0/en')
    if d.get('class') != 'dataset' or 'value' not in d:
        raise ValueError('invalid JSON-stat dataset')
    return {'source': url, 'dataset': d, 'note': '完整保留数据、维度、单位与注释；超 12 MiB 的表不在本接口下载。'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--datefrom', default='2000-01-01')
    a = s.add_parser('dataset')
    a.add_argument('table')
    a = p.parse_args()
    x = search(a.keyword, a.limit, a.datefrom) if a.cmd == 'search' else dataset(a.table)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
