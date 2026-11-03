"""South Africa National Treasury Municipal Money API: cubes and raw facts."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://municipaldata.treasury.gov.za/api/'
MAX = 10 * 1024 * 1024

def _name(x):
    if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}', x):
        raise ValueError('invalid identifier')
    return x

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX:
                raise ValueError('response exceeds 10 MiB')
            parts.append(b)
        d = json.loads(b''.join(parts))
        if d.get('status') != 'ok':
            raise ValueError(str(d))
        return {'source': r.url, 'result': d}

def cubes():
    return _get('cubes')

def metadata(cube):
    return _get('cubes/' + _name(cube) + '/model')

def _cut(filters):
    if not isinstance(filters, dict) or len(filters) > 10:
        raise ValueError('invalid filters')
    out = []
    for k, v in filters.items():
        _name(k)
        if not re.fullmatch('[A-Za-z0-9_.]+\\.[A-Za-z0-9_.]+', k):
            raise ValueError('filter key needs dimension.attribute')
        if isinstance(v, int) and (not isinstance(v, bool)):
            value = str(v)
        elif isinstance(v, str) and re.fullmatch('[A-Za-z0-9_. -]{1,80}', v):
            value = '"' + v + '"'
        else:
            raise ValueError('invalid filter value')
        out.append(k + ':' + value)
    return '|'.join(out)

def facts(cube, filters, page=1, limit=20):
    if not isinstance(page, int) or page < 1 or (not 1 <= limit <= 100) or (not filters):
        raise ValueError('nonempty filters, page >= 1 and limit 1–100 required')
    return _get('cubes/' + _name(cube) + '/facts', {'cut': _cut(filters), 'page': page, 'pagesize': limit})

def members(cube, dimension, page=1, limit=20):
    if page < 1 or not 1 <= limit <= 100:
        raise ValueError('invalid pagination')
    return _get('cubes/' + _name(cube) + '/members/' + _name(dimension), {'page': page, 'pagesize': limit})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('cubes')
    a = s.add_parser('metadata')
    a.add_argument('cube')
    a = s.add_parser('members')
    a.add_argument('cube')
    a.add_argument('dimension')
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('facts')
    a.add_argument('cube')
    a.add_argument('--filters', required=True)
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    x = cubes() if a.cmd == 'cubes' else metadata(a.cube) if a.cmd == 'metadata' else members(a.cube, a.dimension, a.page, a.limit) if a.cmd == 'members' else facts(a.cube, json.loads(a.filters), a.page, a.limit)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
