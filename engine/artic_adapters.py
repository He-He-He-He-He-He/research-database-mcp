"""Art Institute of Chicago artwork search and artwork details (read-only)."""
import release_runtime
import argparse
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.artic.edu/api/v1/artworks'

def _get(url):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise ValueError('unexpected response')
    return data

def search_artworks(query, limit=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be a non-empty string')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1 to 100')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or (page * limit > 10000):
        raise ValueError('page must be positive and page * limit at most 10000')
    fields = 'id,title,artist_display,date_display,is_public_domain'
    data = _get(BASE + '/search?' + urlencode({'q': query.strip(), 'limit': limit, 'page': page, 'fields': fields}))
    if not isinstance(data.get('data'), list):
        raise ValueError('missing data list')
    return data

def get_artwork(artwork_id):
    if isinstance(artwork_id, bool) or not isinstance(artwork_id, int) or artwork_id <= 0:
        raise ValueError('artwork_id must be a positive integer')
    data = _get(BASE + '/' + str(artwork_id))
    if not isinstance(data.get('data'), dict) or data['data'].get('id') != artwork_id:
        raise ValueError('unexpected artwork ID')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=10)
    search.add_argument('--page', type=int, default=1)
    detail = commands.add_parser('detail')
    detail.add_argument('artwork_id', type=int)
    args = parser.parse_args()
    result = search_artworks(args.query, args.limit, args.page) if args.command == 'search' else get_artwork(args.artwork_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
