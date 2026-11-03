"""Search re3data research repository registry and read repository metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://www.re3data.org/api/v40/'
_lock = threading.Lock()
_last = 0.0

def _get(path, params=None):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path + ('?' + urlencode(params) if params else '')], capture_output=True, check=True)
    return ET.fromstring(r.stdout)

def search_repositories(query, limit=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 150:
        raise ValueError('invalid query')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    root = _get('repositories', {'query': query.strip()})
    if root.tag != 'list':
        raise ValueError('unexpected repository index')
    all_items = root.findall('repository')
    return {'matched_in_returned_index': len(all_items), 'items': [{'id': x.findtext('id'), 'name': x.findtext('name'), 'doi': x.findtext('doi')} for x in all_items[:limit]]}

def repository_detail(repo_id):
    if not isinstance(repo_id, str) or not re.fullmatch('r3d[0-9]{9}', repo_id):
        raise ValueError('invalid re3data id')
    root = _get('repository/' + repo_id)
    if root.tag != '{http://www.re3data.org/schema/4-0}re3data':
        raise ValueError('unexpected metadata schema')
    ids = [x.text for x in root.iter() if x.tag.endswith('}re3data') and x is not root]
    if repo_id not in ids:
        raise ValueError('unexpected repository id')
    names = [x.text for x in root.iter() if x.tag.endswith('}repositoryName')]
    return {'id': repo_id, 'names': names, 'metadata_xml': ET.tostring(root, encoding='unicode')}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=10)
    d = sub.add_parser('detail')
    d.add_argument('repo_id')
    a = p.parse_args()
    result = search_repositories(a.query, a.limit) if a.command == 'search' else repository_detail(a.repo_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
