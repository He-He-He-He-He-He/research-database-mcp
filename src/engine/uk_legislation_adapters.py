"""Search UK legislation feeds and read document metadata, read-only."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://www.legislation.gov.uk'
_lock = threading.Lock()
_last = 0.0
NS = {'a': 'http://www.w3.org/2005/Atom', 'dc': 'http://purl.org/dc/elements/1.1/'}

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path], capture_output=True, check=True)
    return ET.fromstring(r.stdout)

def search_acts(title, year):
    if not isinstance(title, str) or not title.strip() or len(title) > 150:
        raise ValueError('invalid title')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1801 <= year <= 2100):
        raise ValueError('invalid year')
    root = _get('/ukpga/' + str(year) + '/data.feed?' + urlencode({'title': title.strip()}))
    if root.tag != '{http://www.w3.org/2005/Atom}feed':
        raise ValueError('unexpected Atom feed')
    return [{'title': x.findtext('a:title', namespaces=NS), 'id': x.findtext('a:id', namespaces=NS), 'updated': x.findtext('a:updated', namespaces=NS)} for x in root.findall('a:entry', NS)]

def act_metadata(year, number):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1801 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(number, bool) or not isinstance(number, int) or (not 1 <= number <= 9999):
        raise ValueError('invalid act number')
    root = _get('/ukpga/' + str(year) + '/' + str(number) + '/data.xml')
    if root.tag != '{http://www.legislation.gov.uk/namespaces/legislation}Legislation':
        raise ValueError('unexpected legislation XML')
    output = {name: root.findtext('.//dc:' + name, namespaces=NS) for name in ('identifier', 'title', 'description', 'language', 'modified')}
    expected = '/ukpga/' + str(year) + '/' + str(number)
    if not output['identifier'] or not output['identifier'].endswith(expected):
        raise ValueError('unexpected act identifier')
    return output

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('title')
    s.add_argument('year', type=int)
    d = sub.add_parser('detail')
    d.add_argument('year', type=int)
    d.add_argument('number', type=int)
    a = p.parse_args()
    result = search_acts(a.title, a.year) if a.command == 'search' else act_metadata(a.year, a.number)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
