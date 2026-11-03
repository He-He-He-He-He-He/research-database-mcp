"""Read-only Zenodo public record search and detail."""
import release_runtime
import argparse
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://zenodo.org/api/records'

def _get(url):
    response = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(response.stdout)
    if not isinstance(data, dict):
        raise ValueError('unexpected Zenodo response')
    return data

def search_records(query, size=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 25):
        raise ValueError('anonymous request size must be 1 to 25')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 400):
        raise ValueError('page must be an integer between 1 and 400')
    data = _get(BASE + '?' + urlencode({'q': query.strip(), 'size': size, 'page': page}))
    if not isinstance(data.get('hits', {}).get('hits'), list):
        raise ValueError('missing search hits')
    return data

def get_record(record_id):
    if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id <= 0:
        raise ValueError('record_id must be a positive integer')
    data = _get(BASE + '/' + str(record_id))
    if data.get('id') != record_id:
        raise ValueError('unexpected record ID')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--size', type=int, default=10)
    search.add_argument('--page', type=int, default=1)
    detail = commands.add_parser('detail')
    detail.add_argument('record_id', type=int)
    args = parser.parse_args()
    result = search_records(args.query, args.size, args.page) if args.command == 'search' else get_record(args.record_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
