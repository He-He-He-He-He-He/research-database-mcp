"""Search UK ONS content and fetch consumer-price time-series details."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
_lock = threading.Lock()
_last = 0.0

def _get(url):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    if not isinstance(data, dict):
        raise ValueError('unexpected ONS response')
    return data

def search(query, limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset must be 0–10000')
    d = _get('https://api.beta.ons.gov.uk/v1/search?' + urlencode({'q': query.strip(), 'limit': limit, 'offset': offset}))
    if not isinstance(d.get('items'), list):
        raise ValueError('missing search items')
    return d

def consumer_price_series(cdid='D7G7'):
    if not isinstance(cdid, str) or not re.fullmatch('[A-Z0-9]{4}', cdid):
        raise ValueError('invalid CDID')
    d = _get('https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/' + cdid.lower() + '/mm23/data')
    if d.get('description', {}).get('cdid') != cdid or not isinstance(d.get('months'), list):
        raise ValueError('unexpected ONS time series')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=10)
    s.add_argument('--offset', type=int, default=0)
    d = sub.add_parser('series')
    d.add_argument('cdid', nargs='?', default='D7G7')
    a = p.parse_args()
    result = search(a.query, a.limit, a.offset) if a.command == 'search' else consumer_price_series(a.cdid)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
