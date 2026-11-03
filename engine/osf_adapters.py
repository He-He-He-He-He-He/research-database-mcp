"""Open Science Framework public project title search and node details."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://api.osf.io/v2/nodes/'
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
    d = json.loads(r.stdout)
    if not isinstance(d, dict) or 'data' not in d:
        raise ValueError('unexpected OSF response')
    return d

def search_projects(title, page_size=10, page=1):
    if not isinstance(title, str) or not title.strip():
        raise ValueError('title must be non-empty')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1–100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1–100')
    d = _get('?' + urlencode({'filter[title]': title.strip(), 'page[size]': page_size, 'page': page}))
    if not isinstance(d['data'], list):
        raise ValueError('unexpected project search result')
    return d

def project_detail(node_id):
    if not isinstance(node_id, str) or not re.fullmatch('[a-z0-9]{5,20}', node_id):
        raise ValueError('invalid OSF node id')
    d = _get(node_id + '/')
    if not isinstance(d['data'], dict) or d['data'].get('id') != node_id:
        raise ValueError('unexpected project id')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('title')
    s.add_argument('--page-size', type=int, default=10)
    s.add_argument('--page', type=int, default=1)
    d = sub.add_parser('detail')
    d.add_argument('node_id')
    a = p.parse_args()
    result = search_projects(a.title, a.page_size, a.page) if a.command == 'search' else project_detail(a.node_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
