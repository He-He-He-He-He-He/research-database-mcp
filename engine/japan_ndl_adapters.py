"""Japan National Diet Library Search OpenSearch and SRU record lookup."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://ndlsearch.ndl.go.jp/api/'
SRU = '{http://www.loc.gov/zing/srw/}'
DC = '{http://purl.org/dc/elements/1.1/}'
_lock = threading.Lock()
_last = 0.0

def _get(path, params):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path + '?' + urlencode(params)], capture_output=True, check=True)
    return ET.fromstring(r.stdout)

def search_titles(title, count=10):
    if not isinstance(title, str) or not title.strip() or len(title) > 150:
        raise ValueError('invalid title')
    if isinstance(count, bool) or not isinstance(count, int) or (not 1 <= count <= 20):
        raise ValueError('count must be 1–20')
    root = _get('opensearch', {'title': title.strip(), 'cnt': count})
    if root.tag != 'rss':
        raise ValueError('unexpected OpenSearch response')
    return [{'title': x.findtext('title'), 'link': x.findtext('link'), 'id': x.findtext('guid')} for x in root.findall('.//item')]

def record(itemno):
    if not isinstance(itemno, str) or not re.fullmatch('R[0-9]{9}-[A-Za-z0-9]{1,80}', itemno):
        raise ValueError('invalid NDL record id')
    root = _get('sru', {'operation': 'searchRetrieve', 'maximumRecords': 2, 'recordPacking': 'xml', 'query': 'itemno="' + itemno + '"'})
    if root.tag != SRU + 'searchRetrieveResponse':
        raise ValueError('unexpected SRU response')
    diagnostics = root.find('.//' + SRU + 'diagnostics')
    if diagnostics is not None:
        raise ValueError('SRU returned diagnostics')
    count = root.findtext(SRU + 'numberOfRecords')
    if count is None:
        raise ValueError('missing result count')
    items = []
    for entry in root.findall('.//' + SRU + 'recordData'):
        fields = {}
        for child in entry.iter():
            if child.tag.startswith(DC):
                fields.setdefault(child.tag[len(DC):], []).append(child.text or '')
        items.append(fields)
    return {'itemno': itemno, 'numberOfRecords': int(count), 'records': items}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('title')
    s.add_argument('--count', type=int, default=10)
    d = sub.add_parser('detail')
    d.add_argument('itemno')
    a = p.parse_args()
    result = search_titles(a.title, a.count) if a.command == 'search' else record(a.itemno)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
