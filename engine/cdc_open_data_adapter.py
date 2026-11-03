"""CDC public Socrata data catalog, dataset metadata and bounded equal-filter rows."""
import release_runtime
import argparse, json, re
import requests
HOST = 'https://data.cdc.gov/'
ID = re.compile('[a-z0-9]{4}-[a-z0-9]{4}')

def _get(url, params=None):
    with requests.get(url, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        try:
            data = json.loads(b''.join(parts))
        except ValueError as e:
            raise ValueError('service did not return JSON') from e
        return {'source': r.url, 'data': data}

def search(keyword, limit=20, offset=0):
    if not keyword or len(keyword) > 100 or (not 1 <= limit <= 50) or (not 0 <= offset <= 10000):
        raise ValueError('invalid search')
    return _get('https://api.us.socrata.com/api/catalog/v1', {'domains': 'data.cdc.gov', 'q': keyword, 'limit': limit, 'offset': offset, 'only': 'datasets'})

def metadata(dataset):
    if not ID.fullmatch(dataset):
        raise ValueError('invalid dataset ID')
    return _get(HOST + 'api/views/' + dataset + '.json')

def rows(dataset, filters, limit=20, offset=0):
    if not filters or len(filters) > 8 or (not 1 <= limit <= 100) or (not 0 <= offset <= 100000):
        raise ValueError('invalid filters or pagination')
    meta = metadata(dataset)['data']
    cols = {c['fieldName'] for c in meta.get('columns', []) if c.get('fieldName') and (not c['fieldName'].startswith(':'))}
    for k, v in filters.items():
        if k not in cols or not re.fullmatch('[A-Za-z0-9_]+', k) or (not v) or (len(v) > 150):
            raise ValueError('invalid field or filter')
    return _get(HOST + 'resource/' + dataset + '.json', {**filters, '$limit': limit, '$offset': offset})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = s.add_parser('metadata')
    a.add_argument('dataset')
    a = s.add_parser('rows')
    a.add_argument('dataset')
    a.add_argument('--filter', action='append', required=True, help='field=value exact match')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    if a.cmd == 'search':
        result = search(a.keyword, a.limit, a.offset)
    elif a.cmd == 'metadata':
        result = metadata(a.dataset)
    else:
        pairs = [x.split('=', 1) for x in a.filter]
        if any((len(x) != 2 for x in pairs)) or len({x[0] for x in pairs}) != len(pairs):
            raise ValueError('invalid or duplicate filter')
        result = rows(a.dataset, dict(pairs), a.limit, a.offset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
