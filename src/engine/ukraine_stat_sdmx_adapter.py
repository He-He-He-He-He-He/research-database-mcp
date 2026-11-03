"""State Statistics Service of Ukraine, SDMX 3.0 catalogue and bounded series."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://stat.gov.ua/sdmx/workspaces/default:integration/registry/sdmx/3.0/'
MAX = 12 * 1024 * 1024

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=45, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX:
                raise ValueError('Response exceeds 12 MiB')
            parts.append(b)
        d = json.loads(b''.join(parts))
        if d.get('status', 200) >= 400:
            raise ValueError(str(d))
        return {'source': r.url, 'result': d}

def _valid(x):
    if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,180}', x) or '..' in x:
        raise ValueError('invalid identifier')
    return x

def search(keyword, limit=20):
    if not keyword or len(keyword) > 120 or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword/limit')
    d = _get('structure/dataflow/*/*/*')
    arr = d['result']['data']['dataflows']
    q = keyword.casefold()
    matches = [x for x in arr if q in (x['id'] + ' ' + str(x.get('names', {}))).casefold()]
    return {'source': d['source'], 'count': len(matches), 'results': matches[:limit]}

def metadata(flow, version):
    return _get('structure/dataflow/SSSU/' + _valid(flow) + '/' + _valid(version), {'references': 'all'})

def data(flow, version, key, last=1):
    _valid(flow)
    _valid(version)
    _valid(key)
    if not 1 <= last <= 100:
        raise ValueError('last 1–100')
    return _get('data/dataflow/SSSU/' + flow + '/' + version + '/' + key, {'lastNObservations': last})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('metadata')
    a.add_argument('flow')
    a.add_argument('version')
    a = s.add_parser('data')
    a.add_argument('flow')
    a.add_argument('version')
    a.add_argument('key')
    a.add_argument('--last', type=int, default=1)
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.flow, a.version) if a.cmd == 'metadata' else data(a.flow, a.version, a.key, a.last)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
