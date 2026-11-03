"""UN Statistics Division SDG public series metadata and country data slice."""
import release_runtime
import argparse
import json
import re
import subprocess
import time
BASE = 'https://unstats.un.org/SDGAPI/v1/sdg/Series'
_last_request = 0.0

def _get(path):
    global _last_request
    delay = 1.0 - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    _last_request = time.monotonic()
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def search_series(query):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    data = _get('/List')
    if not isinstance(data, list):
        raise ValueError('unexpected series list')
    term = query.casefold().strip()
    return [item for item in data if isinstance(item, dict) and (term in str(item.get('description', '')).casefold() or term in str(item.get('code', '')).casefold())]

def series_metadata(code):
    matches = [x for x in search_series(code) if x.get('code') == code]
    if len(matches) != 1:
        raise ValueError('series code not found or ambiguous')
    return matches[0]

def data_slice(code, geo):
    if not isinstance(code, str) or not re.fullmatch('[A-Z0-9_]{1,80}', code):
        raise ValueError('invalid series code')
    if isinstance(geo, bool) or not isinstance(geo, int) or (not 1 <= geo <= 999):
        raise ValueError('geo must be a UN M49 numeric code')
    data = _get('/' + code + '/GeoArea/' + str(geo) + '/DataSlice')
    if not isinstance(data, dict) or data.get('series') != code or str(data.get('geoAreaCode')) != str(geo) or (not isinstance(data.get('dimensions'), list)):
        raise ValueError('unexpected data slice')
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
    data.add_argument('geo', type=int)
    args = parser.parse_args()
    if args.command == 'search':
        result = search_series(args.query)
    elif args.command == 'detail':
        result = series_metadata(args.code)
    else:
        result = data_slice(args.code, args.geo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
