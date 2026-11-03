"""GBIF public species name-usage API: search and retrieve one usage."""
import release_runtime
import argparse
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.gbif.org/v1/species'

def _get(url):
    process = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(process.stdout)
    if not isinstance(data, dict):
        raise ValueError('GBIF returned an unexpected response')
    return data

def search_species(query, limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be a non-empty string')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be an integer between 1 and 100')
    if not isinstance(offset, int) or isinstance(offset, bool) or (not 0 <= offset <= 100000):
        raise ValueError('offset must be an integer between 0 and 100000')
    data = _get(BASE + '/search?' + urlencode({'q': query.strip(), 'limit': limit, 'offset': offset}))
    if not isinstance(data.get('results'), list):
        raise ValueError('GBIF search response has no results list')
    return data

def get_species_usage(key):
    if isinstance(key, bool) or not isinstance(key, int) or key <= 0:
        raise ValueError('key must be a positive integer')
    data = _get(BASE + '/' + str(key))
    if data.get('key') != key:
        raise ValueError('GBIF returned a different usage key')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=10)
    search.add_argument('--offset', type=int, default=0)
    detail = sub.add_parser('detail')
    detail.add_argument('key', type=int)
    args = parser.parse_args()
    data = search_species(args.query, args.limit, args.offset) if args.command == 'search' else get_species_usage(args.key)
    print(json.dumps(data, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
