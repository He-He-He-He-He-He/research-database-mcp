"""GBIF public taxonomy, dataset and bounded occurrence search APIs."""
import release_runtime
import argparse, json, re
import requests
ROOT = 'https://api.gbif.org/v1/'

def _get(path, params):
    with requests.get(ROOT + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(chunk)
        return {'source': r.url, 'data': json.loads(b''.join(parts))}

def species(name):
    if not name or len(name) > 200:
        raise ValueError('invalid scientific name')
    return _get('species/match', {'name': name})

def datasets(query, limit=20, offset=0):
    if not query or len(query) > 150 or (not 1 <= limit <= 100) or (not 0 <= offset <= 10000):
        raise ValueError('invalid search')
    return _get('dataset/search', {'q': query, 'limit': limit, 'offset': offset})

def occurrences(taxon, country, year=None, limit=20, offset=0):
    if not isinstance(taxon, int) or taxon < 1 or (not re.fullmatch('[A-Z]{2}', country)) or (not 1 <= limit <= 100) or (not 0 <= offset) or (offset + limit > 100000):
        raise ValueError('invalid taxon, country or pagination')
    params = {'taxonKey': taxon, 'country': country, 'limit': limit, 'offset': offset}
    if year is not None:
        if not isinstance(year, int) or not 1600 <= year <= 2100:
            raise ValueError('invalid year')
        params['year'] = year
    return _get('occurrence/search', params)

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('species')
    a.add_argument('name')
    a = s.add_parser('datasets')
    a.add_argument('query')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = s.add_parser('occurrences')
    a.add_argument('taxon', type=int)
    a.add_argument('country')
    a.add_argument('--year', type=int)
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    result = species(a.name) if a.cmd == 'species' else datasets(a.query, a.limit, a.offset) if a.cmd == 'datasets' else occurrences(a.taxon, a.country, a.year, a.limit, a.offset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
