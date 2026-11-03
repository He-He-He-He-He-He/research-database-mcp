"""Statistics Canada official WDS public multi-domain statistics API."""
import release_runtime
import argparse, json
import requests
ROOT = 'https://www150.statcan.gc.ca/t1/wds/rest/'

def _request(method, payload=None):
    with requests.request('GET' if payload is None else 'POST', ROOT + method, json=payload, timeout=45, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for x in r.iter_content(65536):
            size += len(x)
            if size > 30 * 1024 * 1024:
                raise ValueError('response exceeds 30 MiB')
            parts.append(x)
        d = json.loads(b''.join(parts))
    if isinstance(d, list) and payload is not None and any((x.get('status') != 'SUCCESS' for x in d)):
        raise ValueError('Statistics Canada returned non-success status: ' + str(d)[:300])
    if isinstance(d, dict) and d.get('status') not in (None, 'SUCCESS'):
        raise ValueError('Statistics Canada returned non-success status')
    return {'source': ROOT + method, 'data': d}

def search(keyword, limit=20, *, offset=0):
    if not keyword or len(keyword) > 150 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('invalid search')
    d = _request('getAllCubesListLite')
    records = [x for x in d['data'] if keyword.casefold() in (x.get('cubeTitleEn') or '').casefold()]
    return {'source': d['source'], 'total': len(records), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(records) else None, 'data': records[offset:offset + limit], 'note': 'The source directory is fetched in full each time and sliced locally; ordering may change between requests.'}

def cube(product):
    if not isinstance(product, int) or not 10000000 <= product <= 99999999:
        raise ValueError('invalid product ID')
    return _request('getCubeMetadata', [{'productId': product}])

def series(vector):
    if not isinstance(vector, int) or vector < 1:
        raise ValueError('invalid vector')
    return _request('getSeriesInfoFromVector', [{'vectorId': vector}])

def observations(vector, latest=12):
    if not isinstance(vector, int) or vector < 1 or (not 1 <= latest <= 100):
        raise ValueError('invalid vector or latest period count')
    return _request('getDataFromVectorsAndLatestNPeriods', [{'vectorId': vector, 'latestN': latest}])

def codes():
    return _request('getCodeSets')

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('cube')
    a.add_argument('product', type=int)
    a = s.add_parser('series')
    a.add_argument('vector', type=int)
    a = s.add_parser('observations')
    a.add_argument('vector', type=int)
    a.add_argument('--latest', type=int, default=12)
    s.add_parser('codes')
    a = p.parse_args()
    result = search(a.keyword, a.limit) if a.cmd == 'search' else cube(a.product) if a.cmd == 'cube' else series(a.vector) if a.cmd == 'series' else observations(a.vector, a.latest) if a.cmd == 'observations' else codes()
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
