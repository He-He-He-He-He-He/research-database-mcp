"""WFP ADAM public hazard-event collections and country-filtered records."""
import release_runtime
import argparse, base64, json, re
import requests
BASE = 'https://api.adam.geospatial.wfp.org/api/'
MAX = 8 * 1024 * 1024

def _name(x):
    if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}', x) or '..' in x:
        raise ValueError('invalid collection ID')
    return x

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX:
                raise ValueError('response exceeds 8 MiB')
            chunks.append(b)
        raw = b''.join(chunks)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = json.loads(base64.b64decode(raw, validate=True))
        return {'source': r.url, 'result': data}

def collections():
    return _get('collections', {'f': 'json'})

def metadata(collection):
    return _get('collections/' + _name(collection), {'f': 'json'})

def queryables(collection):
    return _get('collections/' + _name(collection) + '/queryables', {'f': 'schemajson'})

def items(collection, country, limit=20, offset=0):
    if not re.fullmatch('[A-Z]{3}', country) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('ISO3 uppercase country and bounded pagination required')
    if 'iso3' not in queryables(collection)['result'].get('properties', {}):
        raise ValueError('collection has no iso3 filter')
    return _get('collections/' + _name(collection) + '/items', {'f': 'json', 'filter': "iso3 = '" + country + "'", 'limit': limit, 'offset': offset})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('collections')
    for name in ('metadata', 'queryables'):
        a = s.add_parser(name)
        a.add_argument('collection')
    a = s.add_parser('items')
    a.add_argument('collection')
    a.add_argument('country')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    x = collections() if a.cmd == 'collections' else metadata(a.collection) if a.cmd == 'metadata' else queryables(a.collection) if a.cmd == 'queryables' else items(a.collection, a.country, a.limit, a.offset)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
