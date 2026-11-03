"""Internet Archive item discovery and metadata, read-only."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode

def _get(url):
    process = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    value = json.loads(process.stdout)
    if not isinstance(value, dict):
        raise ValueError('unexpected Internet Archive response')
    return value

def search_items(query, rows=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 100):
        raise ValueError('rows must be 1 to 100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1 to 100')
    params = [('q', query.strip()), ('fl[]', 'identifier'), ('fl[]', 'title'), ('fl[]', 'creator'), ('fl[]', 'year'), ('fl[]', 'mediatype'), ('rows', rows), ('page', page), ('output', 'json')]
    data = _get('https://archive.org/advancedsearch.php?' + urlencode(params))
    if not isinstance(data.get('response', {}).get('docs'), list):
        raise ValueError('missing response docs')
    return data

def get_item(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', identifier):
        raise ValueError('invalid Internet Archive identifier')
    data = _get('https://archive.org/metadata/' + identifier)
    if data.get('metadata', {}).get('identifier') != identifier:
        raise ValueError('item missing or identifier does not match')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--rows', type=int, default=10)
    search.add_argument('--page', type=int, default=1)
    detail = commands.add_parser('detail')
    detail.add_argument('identifier')
    args = parser.parse_args()
    result = search_items(args.query, args.rows, args.page) if args.command == 'search' else get_item(args.identifier)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
