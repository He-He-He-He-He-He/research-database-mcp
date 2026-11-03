"""UNHCR Refugee Data Portal catalogue, metadata and paged observations."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api-data.unhcr.org/api/v0'

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if not isinstance(data, dict) or 'data' not in data:
        raise ValueError('unexpected UNHCR response')
    return data

def _code(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', code):
        raise ValueError('invalid data series code')
    return code

def search_series(query, page=1, page_size=10):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must not be empty')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1–100')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1–100')
    data = _get('/catalog', {'q': query.strip(), 'page': page, 'page_size': page_size})
    if not isinstance(data['data'], list):
        raise ValueError('unexpected catalogue')
    return data

def series_metadata(code):
    code = _code(code)
    data = _get('/metadata/' + code)
    if not isinstance(data['data'], dict) or data['data'].get('code') != code:
        raise ValueError('unexpected series metadata')
    return data

def series_data(code, pop_type, country, since, page=1, page_size=10):
    code = _code(code)
    if not re.fullmatch('[A-Z0-9_]{1,30}', pop_type) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('invalid population type or country code')
    if isinstance(since, bool) or not isinstance(since, int) or (not 1950 <= since <= 2100):
        raise ValueError('since must be a year from 1950 to 2100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1–100')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1–100')
    data = _get('/data/' + code, {'c[pop_type]': pop_type, 'c[ref_area_adm0]': country, 'time_period': 'ge:' + str(since), 'dimensions': 'default', 'page': page, 'page_size': page_size})
    if not isinstance(data['data'], list):
        raise ValueError('unexpected data response')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    detail = commands.add_parser('detail')
    detail.add_argument('code')
    data = commands.add_parser('data')
    data.add_argument('code')
    data.add_argument('pop_type')
    data.add_argument('country')
    data.add_argument('since', type=int)
    data.add_argument('--page', type=int, default=1)
    data.add_argument('--page-size', type=int, default=10)
    args = parser.parse_args()
    if args.command == 'search':
        result = search_series(args.query)
    elif args.command == 'detail':
        result = series_metadata(args.code)
    else:
        result = series_data(args.code, args.pop_type, args.country, args.since, args.page, args.page_size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
