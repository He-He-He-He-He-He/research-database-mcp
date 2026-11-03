"""US DOE OSTI funded research records: public search and record detail."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://www.osti.gov/api/v1/records'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--header', 'Accept: application/json', BASE + path], capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    if not isinstance(data, list):
        raise ValueError('unexpected OSTI response')
    return data

def search_records(query, rows=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 100):
        raise ValueError('rows must be 1–100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('page must be 1–1000')
    return _get('?' + urlencode({'q': query.strip(), 'rows': rows, 'page': page}))

def record_detail(osti_id):
    if not isinstance(osti_id, str) or not re.fullmatch('[0-9]{1,15}', osti_id):
        raise ValueError('invalid OSTI id')
    d = _get('/' + osti_id)
    if len(d) != 1 or str(d[0].get('osti_id')) != osti_id:
        raise ValueError('unexpected OSTI record')
    return d[0]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--rows', type=int, default=10)
    s.add_argument('--page', type=int, default=1)
    d = sub.add_parser('detail')
    d.add_argument('osti_id')
    a = p.parse_args()
    result = search_records(a.query, a.rows, a.page) if a.command == 'search' else record_detail(a.osti_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
