"""Dryad public dataset metadata search and detail by DOI."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import quote, urlencode
BASE = 'https://datadryad.org/api/v2/'
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
    if not isinstance(d, dict):
        raise ValueError('unexpected Dryad response')
    return d

def search_datasets(query, page_size=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1–100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('page must be 1–1000')
    d = _get('search?' + urlencode({'q': query.strip(), 'per_page': page_size, 'page': page}))
    if not isinstance(d.get('_embedded', {}).get('stash:datasets'), list):
        raise ValueError('missing search datasets')
    return d

def dataset_detail(doi):
    if not isinstance(doi, str) or not re.fullmatch('doi:10\\.[0-9]{4,9}/[A-Za-z0-9._;()/-]{1,120}', doi):
        raise ValueError('invalid DOI')
    d = _get('datasets/' + quote(doi, safe=''))
    if d.get('identifier') != doi:
        raise ValueError('unexpected DOI')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--page-size', type=int, default=10)
    s.add_argument('--page', type=int, default=1)
    d = sub.add_parser('detail')
    d.add_argument('doi')
    a = p.parse_args()
    result = search_datasets(a.query, a.page_size, a.page) if a.command == 'search' else dataset_detail(a.doi)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
