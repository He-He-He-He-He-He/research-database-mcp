"""Stats NZ published bulk CSV catalogue, with local bounded filtering."""
import release_runtime
import argparse, csv, io, json, re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import requests
ROOT = 'https://www.stats.govt.nz'
PAGE = ROOT + '/large-datasets/csv-files-for-download/'

class Embedded(HTMLParser):

    def __init__(self):
        super().__init__()
        self.payloads = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'div' and d.get('data-value', '').startswith('{') and ('PageBlocks' in d['data-value']):
            self.payloads.append(d['data-value'])

def get(url, maxbytes):
    s = requests.Session()
    s.trust_env = False
    with s.get(url, timeout=40, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > maxbytes:
                raise ValueError('Response exceeds size limit')
        return (bytes(buf), r.url)

def catalog(keyword=''):
    b, url = get(PAGE, 4000000)
    p = Embedded()
    p.feed(b.decode('utf-8-sig'))
    if not p.payloads:
        raise ValueError('No embedded catalogue')
    items = []
    seen = set()

    def walk(x):
        if isinstance(x, dict):
            if x.get('DocumentExtension') in ['csv', 'zip'] and x.get('ID') and x.get('DocumentLink'):
                if x['ID'] not in seen:
                    seen.add(x['ID'])
                    items.append({k: x.get(k) for k in ['ID', 'Title', 'DocumentLink', 'DocumentSize', 'DocumentExtension']})
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    for raw in p.payloads:
        walk(json.loads(raw))
    matches = [x for x in items if keyword.casefold() in str(x['Title']).casefold()]
    return {'source': url, 'count': len(matches), 'items': matches}

def data(id, filters, limit):
    if not re.fullmatch('\\d{1,10}', id) or not 1 <= limit <= 1000:
        raise ValueError('Invalid id or limit')
    hits = [x for x in catalog()['items'] if x['ID'] == id]
    if len(hits) != 1 or hits[0]['DocumentExtension'] != 'csv':
        raise ValueError('Select a CSV id in current catalogue; ZIP not supported')
    item = hits[0]
    url = urljoin(ROOT, item['DocumentLink'])
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != 'www.stats.govt.nz' or (not p.path.startswith('/assets/')):
        raise ValueError('Unexpected file host or path')
    b, url = get(url, 25000000)
    reader = csv.DictReader(io.StringIO(b.decode('utf-8-sig')))
    selection = {}
    for f in filters:
        if '=' not in f:
            raise ValueError('Use FIELD=VALUE')
        k, v = f.split('=', 1)
        if k not in (reader.fieldnames or []):
            raise ValueError('Unknown CSV field ' + k)
        selection[k] = v
    rows = []
    count = 0
    for row in reader:
        if all((row.get(k) == v for k, v in selection.items())):
            count += 1
            if len(rows) < limit:
                rows.append(row)
    return {'source': url, 'catalog_item': item, 'fields': reader.fieldnames, 'matches': count, 'returned': len(rows), 'truncated': count > len(rows), 'rows': rows, 'note': 'CSV is downloaded in full then filtered locally. Check accompanying release and notes for unit, revisions and methodology.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    c = s.add_parser('catalog')
    c.add_argument('keyword', nargs='?', default='')
    d = s.add_parser('data')
    d.add_argument('id')
    d.add_argument('--filter', action='append', default=[])
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(catalog(a.keyword) if a.command == 'catalog' else data(a.id, a.filter, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
