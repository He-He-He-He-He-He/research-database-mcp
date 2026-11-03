"""Discover PANGAEA research datasets via DataCite and read PANGAEA OAI metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
_lock = threading.Lock()
_last = 0.0

def _get(url):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, check=True)
    return r.stdout

def search_datasets(query, limit=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 150:
        raise ValueError('invalid query')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    url = 'https://api.datacite.org/dois?' + urlencode({'query': '(' + query.strip() + ') AND prefix:10.1594', 'page[size]': limit})
    d = json.loads(_get(url))
    if not isinstance(d, dict) or not isinstance(d.get('data'), list):
        raise ValueError('unexpected DataCite response')
    d['data'] = [x for x in d['data'] if str(x.get('id', '')).lower().startswith('10.1594/pangaea.')]
    return d

def dataset_metadata(number):
    if not isinstance(number, str) or not re.fullmatch('[0-9]{1,12}', number):
        raise ValueError('number must be numeric PANGAEA identifier')
    doi = '10.1594/PANGAEA.' + number
    url = 'https://ws.pangaea.de/oai/provider?' + urlencode({'verb': 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': 'oai:pangaea.de:doi:' + doi})
    root = ET.fromstring(_get(url))
    errors = [x for x in root.iter() if x.tag.endswith('}error')]
    if errors:
        raise ValueError('PANGAEA OAI error: ' + str(errors[0].get('code')))
    identifiers = [x.text or '' for x in root.iter() if x.tag.endswith('}identifier')]
    if not any((doi.lower() in x.lower() for x in identifiers)):
        raise ValueError('unexpected record identifier')
    return {'doi': doi, 'metadata_xml': ET.tostring(root, encoding='unicode')}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=10)
    d = sub.add_parser('detail')
    d.add_argument('number')
    a = p.parse_args()
    result = search_datasets(a.query, a.limit) if a.command == 'search' else dataset_metadata(a.number)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
