"""Read-only OpenAIRE Graph research product search and detail."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import quote, urlencode
BASE = 'https://api.openaire.eu/graph/v3/research-products'
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
        raise ValueError('unexpected OpenAIRE response')
    return d

def search_products(query, page_size=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1–100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1–100')
    d = _get('?' + urlencode({'search': query.strip(), 'pageSize': page_size, 'page': page}))
    if not isinstance(d.get('results'), list):
        raise ValueError('missing results')
    return d

def product_detail(product_id):
    if not isinstance(product_id, str) or not re.fullmatch('[A-Za-z0-9_:-]{1,120}', product_id):
        raise ValueError('invalid OpenAIRE id')
    d = _get('/' + quote(product_id, safe=''))
    if d.get('id') != product_id:
        raise ValueError('unexpected product id')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--page-size', type=int, default=10)
    s.add_argument('--page', type=int, default=1)
    d = sub.add_parser('detail')
    d.add_argument('product_id')
    a = p.parse_args()
    result = search_products(a.query, a.page_size, a.page) if a.command == 'search' else product_detail(a.product_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
