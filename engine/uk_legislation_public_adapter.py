"""UK legislation.gov.uk official Atom search and section XML."""
import release_runtime
import argparse, json, re, xml.etree.ElementTree as ET
import requests
ROOT = 'https://www.legislation.gov.uk/'
A = '{http://www.w3.org/2005/Atom}'
TYPES = {'ukpga', 'uksi', 'asp', 'ssi', 'anaw', 'asc', 'wsi', 'nia', 'nisr'}

def _get(path, params=None):
    with requests.get(ROOT + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 3 * 1024 * 1024:
                raise ValueError('response exceeds 3 MiB')
            parts.append(c)
        return (r.url, b''.join(parts))

def search(kind, title, page=1):
    if kind not in TYPES or not title or len(title) > 150 or (not 1 <= page <= 1000):
        raise ValueError('invalid type, title or page')
    source, raw = _get(kind + '/data.feed', {'title': title, 'page': page})
    root = ET.fromstring(raw)
    if root.tag != A + 'feed':
        raise ValueError('unexpected Atom feed')
    data = []
    for e in root.findall(A + 'entry'):
        links = []
        for l in e.findall(A + 'link'):
            url = l.get('href', '')
            if url.startswith('http://www.legislation.gov.uk/'):
                url = 'https://' + url[7:]
            links.append({'rel': l.get('rel'), 'type': l.get('type'), 'href': url})
        data.append({'title': e.findtext(A + 'title'), 'id': e.findtext(A + 'id'), 'published': e.findtext(A + 'published'), 'updated': e.findtext(A + 'updated'), 'summary': e.findtext(A + 'summary'), 'links': links})
    return {'source': source, 'entries': data, 'page': page, 'note': 'Feed normally sorted by last modification date; updated is not enactment date.'}

def section(kind, year, number, section):
    if kind not in TYPES or not 1200 <= year <= 2100 or (not 1 <= number <= 999999) or (not re.fullmatch('[0-9]{1,5}[A-Za-z]{0,2}', section)):
        raise ValueError('invalid legislation reference')
    source, raw = _get(f'{kind}/{year}/{number}/section/{section}/data.xml')
    root = ET.fromstring(raw)
    if not root.tag.endswith('Legislation'):
        raise ValueError('unexpected legislation XML')
    return {'source': source, 'xml': raw.decode('utf-8-sig'), 'note': 'Official XML as served; version, geographical extent and amendment status must be checked.'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('kind', choices=sorted(TYPES))
    a.add_argument('title')
    a.add_argument('--page', type=int, default=1)
    a = s.add_parser('section')
    a.add_argument('kind', choices=sorted(TYPES))
    a.add_argument('year', type=int)
    a.add_argument('number', type=int)
    a.add_argument('section')
    a = p.parse_args()
    d = search(a.kind, a.title, a.page) if a.cmd == 'search' else section(a.kind, a.year, a.number, a.section)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
