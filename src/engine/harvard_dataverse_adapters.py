"""Harvard Dataverse public dataset search and latest published metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://dataverse.harvard.edu/api/'
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
    data = json.loads(r.stdout)
    if not isinstance(data, dict) or data.get('status') != 'OK' or (not isinstance(data.get('data'), dict)):
        raise ValueError('unexpected Dataverse response')
    return data['data']

def search_datasets(query, count=10, start=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(count, bool) or not isinstance(count, int) or (not 1 <= count <= 100):
        raise ValueError('count must be 1–100')
    if isinstance(start, bool) or not isinstance(start, int) or (not 0 <= start <= 10000):
        raise ValueError('start must be 0–10000')
    d = _get('search', {'q': query.strip(), 'type': 'dataset', 'per_page': count, 'start': start})
    if not isinstance(d.get('items'), list):
        raise ValueError('missing search items')
    return d

def published_dataset(doi):
    if not isinstance(doi, str) or not re.fullmatch('doi:10\\.[0-9]{4,9}/[A-Za-z0-9._;()/-]{1,120}', doi):
        raise ValueError('invalid DOI')
    d = _get('datasets/:persistentId/versions/:latest-published', {'persistentId': doi})
    if d.get('datasetPersistentId') != doi or d.get('versionState') != 'RELEASED':
        raise ValueError('unexpected dataset or version')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--count', type=int, default=10)
    s.add_argument('--start', type=int, default=0)
    d = sub.add_parser('detail')
    d.add_argument('doi')
    a = p.parse_args()
    result = search_datasets(a.query, a.count, a.start) if a.command == 'search' else published_dataset(a.doi)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
