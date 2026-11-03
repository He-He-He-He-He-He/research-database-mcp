"""Argentina official national time-series API: catalog search and values."""
import release_runtime
import argparse, json, re
import requests
ROOT = 'https://apis.datos.gob.ar/series/api/'

def _get(path, params):
    with requests.get(ROOT + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for c in r.iter_content(65536):
            n += len(c)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        try:
            data = json.loads(b''.join(parts))
        except ValueError:
            raise ValueError('service did not return JSON') from None
        return {'source': r.url, 'data': data}

def search(keyword, limit=20, offset=0):
    if not keyword or len(keyword) > 150 or (not 1 <= limit <= 100) or (not 0 <= offset <= 10000):
        raise ValueError('invalid search')
    result = _get('search', {'q': keyword, 'limit': limit, 'start': offset})
    if result['data'].get('start') != offset:
        raise ValueError('service returned unexpected search offset')
    return result

def series(id, latest=12):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,120}', id) or not 1 <= latest <= 100:
        raise ValueError('invalid series ID or latest period count')
    return _get('series', {'ids': id, 'last': latest, 'format': 'json'})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = s.add_parser('series')
    a.add_argument('id')
    a.add_argument('--latest', type=int, default=12)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.limit, a.offset) if a.cmd == 'search' else series(a.id, a.latest), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
