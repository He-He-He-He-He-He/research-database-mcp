"""World Bank development data catalog search and metadata, read-only."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://ddh-openapi.worldbank.org/'
_lock = threading.Lock()
_last = 0.0

def _get(path, params=None):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        url = BASE + path + ('?' + urlencode(params) if params else '')
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    if not isinstance(d, dict):
        raise ValueError('unexpected catalog response')
    return d

def search_datasets(query, limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset must be 0–10000')
    d = _get('search', {'qname': 'dataset', 'param': query.strip(), 'top': limit, 'skip': offset})
    if not isinstance(d.get('data'), list):
        raise ValueError('missing catalog results')
    d['toolkit_pagination_note'] = 'World Bank relevance ordering can vary between requests, even for the same query; offset pages may overlap or omit records. Deduplicating alone cannot recover missing records. Results are not guaranteed exhaustive; recheck the official source.'
    return d

def dataset_metadata(dataset_id):
    if not isinstance(dataset_id, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', dataset_id):
        raise ValueError('invalid dataset id')
    d = _get('datasets/' + dataset_id)
    if d.get('dataset_unique_id') != dataset_id:
        raise ValueError('unexpected dataset id')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=10)
    s.add_argument('--offset', type=int, default=0)
    t = sub.add_parser('detail')
    t.add_argument('dataset_id')
    a = p.parse_args()
    result = search_datasets(a.query, a.limit, a.offset) if a.command == 'search' else dataset_metadata(a.dataset_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
