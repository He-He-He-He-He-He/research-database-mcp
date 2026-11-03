"""UNIDO SDG 9 industry country profiles, read-only."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
BASE = 'https://stat.unido.org/portal/sdg'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path], capture_output=True, text=True, check=True)
    result = json.loads(r.stdout)
    if not isinstance(result, dict):
        raise ValueError('unexpected UNIDO response')
    return result

def countries(query=''):
    if not isinstance(query, str):
        raise ValueError('query must be a string')
    result = _get('/countries')
    data = result.get('data')
    if not isinstance(data, list):
        raise ValueError('missing countries')
    q = query.casefold().strip()
    return [x for x in data if q in str(x.get('name', '')).casefold() or q == str(x.get('iso3', '')).casefold() or q == str(x.get('code', '')).casefold()]

def country_profile(code):
    if not isinstance(code, str) or not re.fullmatch('[0-9]{3}', code):
        raise ValueError('country code must be three digits, e.g. 156')
    result = _get('/' + code)
    if result.get('code') != code or not isinstance(result.get('variables'), list) or (not isinstance(result.get('graphData'), list)):
        raise ValueError('missing or mismatched UNIDO country profile')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    q = sub.add_parser('countries')
    q.add_argument('query', nargs='?', default='')
    p = sub.add_parser('profile')
    p.add_argument('code')
    args = parser.parse_args()
    result = countries(args.query) if args.command == 'countries' else country_profile(args.code)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
