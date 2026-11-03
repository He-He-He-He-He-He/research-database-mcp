"""IOC-UNESCO OBIS marine species, dataset and occurrence API."""
import release_runtime
import argparse, json
from urllib.parse import quote
import requests
ROOT = 'https://api.obis.org/v3/'

def _get(path, params=None):
    with requests.get(ROOT + path, params=params, timeout=40, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for c in r.iter_content(65536):
            n += len(c)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        return {'source': r.url, 'data': json.loads(b''.join(parts))}

def _name(name):
    if not isinstance(name, str) or not name.strip() or len(name) > 150 or any((c in name for c in '\r\n/')):
        raise ValueError('invalid scientific name')
    return name.strip()

def taxon(name):
    return _get('taxon/' + quote(_name(name), safe=''))

def occurrences(name, limit=20):
    if not 1 <= limit <= 100:
        raise ValueError('limit must be 1–100')
    return _get('occurrence', {'scientificname': _name(name), 'size': limit})

def datasets(name, limit=20):
    if not 1 <= limit <= 100:
        raise ValueError('limit must be 1–100')
    return _get('dataset', {'scientificname': _name(name), 'size': limit})

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    for cmd in ['taxon', 'occurrences', 'datasets']:
        a = sub.add_parser(cmd)
        a.add_argument('name')
        if cmd != 'taxon':
            a.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    result = taxon(a.name) if a.cmd == 'taxon' else occurrences(a.name, a.limit) if a.cmd == 'occurrences' else datasets(a.name, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
