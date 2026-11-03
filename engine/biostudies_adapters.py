"""EMBL-EBI BioStudies public search and study metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://www.ebi.ac.uk/biostudies/api/v1/'
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
        raise ValueError('unexpected BioStudies response')
    return d

def search_studies(query, page_size=10, page=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must not be empty')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1–100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1–100')
    d = _get('search?' + urlencode({'query': query.strip(), 'pageSize': page_size, 'page': page}))
    if not isinstance(d.get('hits'), list):
        raise ValueError('missing search hits')
    return d

def study_detail(accession):
    if not isinstance(accession, str) or not re.fullmatch('[A-Z][A-Z0-9-]{2,50}', accession):
        raise ValueError('invalid accession')
    d = _get('studies/' + accession)
    if d.get('accno') != accession:
        raise ValueError('unexpected accession')
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--page-size', type=int, default=10)
    s.add_argument('--page', type=int, default=1)
    d = sub.add_parser('detail')
    d.add_argument('accession')
    a = p.parse_args()
    result = search_studies(a.query, a.page_size, a.page) if a.command == 'search' else study_detail(a.accession)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
