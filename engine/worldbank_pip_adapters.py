"""World Bank PIP country-year poverty observations and parameter metadata."""
import release_runtime
import argparse
import json
import math
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://api.worldbank.org/pip/v1/'
_lock = threading.Lock()
_last = 0.0

def _get(path, params):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path + '?' + urlencode(params)], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    if not isinstance(d, list):
        raise ValueError('unexpected PIP response')
    return d

def valid_parameters():
    return _get('valid-params', {'endpoint': 'pip', 'format': 'json'})

def poverty(country, year, line):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('invalid country code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(line, bool) or not isinstance(line, (float, int)) or (not math.isfinite(line)) or (not 0 <= line <= 2700):
        raise ValueError('invalid poverty line')
    d = _get('pip', {'country': country, 'year': year, 'povline': line, 'format': 'json'})
    if any((x.get('country_code') != country or x.get('reporting_year') != year for x in d)):
        raise ValueError('unexpected country or year')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('parameters')
    q = sub.add_parser('data')
    q.add_argument('country')
    q.add_argument('year', type=int)
    q.add_argument('line', type=float)
    a = p.parse_args()
    result = valid_parameters() if a.command == 'parameters' else poverty(a.country, a.year, a.line)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
