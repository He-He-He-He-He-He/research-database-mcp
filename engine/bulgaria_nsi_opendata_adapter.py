"""Bulgarian NSI public Infostat datasets in JSON-stat 2.0."""
import release_runtime
import argparse, itertools, json, re
from html.parser import HTMLParser
import requests
BASE = 'https://www.nsi.bg/opendata/'

class CatalogParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.inrow = False
        self.bold = False
        self.name = []
        self.did = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.inrow = True
            self.name = []
            self.did = None
        if self.inrow and tag == 'b':
            self.bold = True
        if self.inrow and tag == 'a':
            m = re.search('getopendata_json\\.php\\?[^\\"]*\\bid=(\\d+)', dict(attrs).get('href', ''))
            if m:
                self.did = int(m.group(1))

    def handle_endtag(self, tag):
        if tag == 'b':
            self.bold = False
        if tag == 'tr':
            if self.did is not None:
                self.items.append({'id': self.did, 'name': ' '.join(' '.join(self.name).split())})
            self.inrow = False

    def handle_data(self, data):
        if self.bold:
            self.name.append(data)

def get(path, params):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for chunk in r.iter_content(65536):
            b.extend(chunk)
            if len(b) > 12000000:
                raise ValueError('Response exceeds 12 MB')
        return (bytes(b), r.url)

def catalog(keyword=''):
    b, url = get('', {'l': 'en'})
    p = CatalogParser()
    p.feed(b.decode('utf-8', errors='replace'))
    items = [x for x in p.items if keyword.casefold() in x['name'].casefold()]
    return {'source': url, 'count': len(items), 'datasets': items}

def dataset(id):
    if not 1 <= id <= 999999:
        raise ValueError('Invalid dataset id')
    b, url = get('getopendata_json.php', {'l': 'en', 'id': id})
    j = json.loads(b)
    if j.get('class') != 'dataset' or not j.get('id'):
        raise ValueError('Unexpected JSON-stat dataset')
    return (j, url)

def dimensions(j):
    out = []
    for key, size in zip(j['id'], j['size']):
        x = j['dimension'][key]
        cat = x['category']
        idx = cat.get('index')
        labels = cat.get('label', {})
        if isinstance(idx, dict):
            codes = sorted(idx, key=idx.get)
        elif isinstance(idx, list):
            codes = idx
        else:
            codes = list(labels)
        if len(codes) != size:
            raise ValueError('Unexpected category index for ' + key)
        out.append({'id': key, 'label': x.get('label'), 'codes': codes, 'labels': labels})
    return out

def metadata(id):
    j, url = dataset(id)
    return {'source': url, 'label': j.get('label'), 'updated': j.get('updated'), 'source_description': j.get('source'), 'extension': j.get('extension'), 'dimensions': dimensions(j), 'units_and_notes': j.get('dimension'), 'status': j.get('status')}

def data(id, filters, limit):
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1–1000')
    j, url = dataset(id)
    dims = dimensions(j)
    selected = {}
    for pair in filters:
        if '=' not in pair:
            raise ValueError('Expected DIMENSION=CODE')
        k, v = pair.split('=', 1)
        dim = next((d for d in dims if d['id'] == k), None)
        if not dim or v not in dim['codes']:
            raise ValueError('Unknown dimension or code: ' + pair)
        selected[k] = v
    values = j.get('value', [])
    status = j.get('status')
    rows = []
    count = 0
    ranges = [[d['codes'].index(selected[d['id']])] if d['id'] in selected else range(len(d['codes'])) for d in dims]
    for indexes in itertools.product(*ranges):
        pos = 0
        for n, i in zip(j['size'], indexes):
            pos = pos * n + i
        value = values[pos] if isinstance(values, list) and pos < len(values) else values.get(str(pos)) if isinstance(values, dict) else None
        if value is None:
            continue
        count += 1
        if len(rows) < limit:
            coords = {d['id']: {'code': d['codes'][i], 'label': d['labels'].get(d['codes'][i])} for d, i in zip(dims, indexes)}
            st = status[pos] if isinstance(status, list) and pos < len(status) else status.get(str(pos)) if isinstance(status, dict) else status
            rows.append({'dimensions': coords, 'value': value, 'status': st})
    return {'source': url, 'label': j.get('label'), 'updated': j.get('updated'), 'matches_non_null': count, 'returned': len(rows), 'truncated': count > len(rows), 'rows': rows, 'note': 'Values and status are kept as published, including parenthesized values; consult methodology and code lists.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('keyword', nargs='?', default='')
    m = s.add_parser('metadata')
    m.add_argument('id', type=int)
    d = s.add_parser('data')
    d.add_argument('id', type=int)
    d.add_argument('--filter', action='append', default=[])
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(catalog(a.keyword) if a.cmd == 'catalog' else metadata(a.id) if a.cmd == 'metadata' else data(a.id, a.filter, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
