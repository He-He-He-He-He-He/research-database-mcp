"""WHO NCD Microdata Repository: bounded catalog search and study metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode, quote
BASE = 'https://extranet.who.int/ncdsmicrodata/index.php/api/catalog/'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        body = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', '10000000', BASE + path], capture_output=True, check=True).stdout
    if len(body) > 10000000:
        raise ValueError('response exceeds size limit')
    data = json.loads(body)
    if data.get('status', 'success') != 'success':
        raise ValueError('upstream returned unsuccessful response')
    return data

def search(query, limit=5):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('query must contain 1–200 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    data = _get('search?' + urlencode({'sk': query, 'ps': limit}))
    if not isinstance(data.get('result', {}).get('rows'), list):
        raise ValueError('unexpected search response')
    return data['result']

def detail(idno):
    if not isinstance(idno, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,200}', idno):
        raise ValueError('invalid dataset idno')
    data = _get(quote(idno, safe=''))
    dataset = data.get('dataset')
    if not isinstance(dataset, dict) or dataset.get('idno') != idno:
        raise ValueError('unexpected dataset')
    return dataset

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('search')
    q.add_argument('query')
    q.add_argument('--limit', type=int, default=5)
    q = s.add_parser('detail')
    q.add_argument('idno')
    a = p.parse_args()
    print(json.dumps(search(a.query, a.limit) if a.command == 'search' else detail(a.idno), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
