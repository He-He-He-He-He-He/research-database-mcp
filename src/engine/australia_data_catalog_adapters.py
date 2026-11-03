"""Read-only data.gov.au public dataset search and metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://data.gov.au/data/api/3/action/'
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
    if not isinstance(d, dict) or d.get('success') is not True:
        raise ValueError('data.gov.au API error')
    return d.get('result')

def search_datasets(query, rows=10, start=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 100):
        raise ValueError('rows must be 1–100')
    if isinstance(start, bool) or not isinstance(start, int) or (not 0 <= start <= 10000):
        raise ValueError('start must be 0–10000')
    d = _get('package_search', {'q': query.strip(), 'rows': rows, 'start': start})
    if not isinstance(d, dict) or not isinstance(d.get('results'), list):
        raise ValueError('unexpected catalog search')
    return d

def dataset_detail(dataset_id):
    if not isinstance(dataset_id, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', dataset_id):
        raise ValueError('invalid dataset id')
    d = _get('package_show', {'id': dataset_id})
    if not isinstance(d, dict) or dataset_id not in (d.get('name'), d.get('id')):
        raise ValueError('unexpected dataset')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--rows', type=int, default=10)
    s.add_argument('--start', type=int, default=0)
    d = sub.add_parser('detail')
    d.add_argument('dataset_id')
    a = p.parse_args()
    result = search_datasets(a.query, a.rows, a.start) if a.command == 'search' else dataset_detail(a.dataset_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
