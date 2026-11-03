"""Deutsche Bundesbank SDMX statistical API."""
import release_runtime
import argparse, csv, io, json, re, xml.etree.ElementTree as ET
import requests
BASE = 'https://api.statistiken.bundesbank.de/rest'

def get(path, params=None):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 10000000:
                raise ValueError('Response exceeds 10 MB; narrow selection')
        return (bytes(buf), r.url)

def catalog(query=''):
    b, u = get('/metadata/dataflow/BBK')
    root = ET.fromstring(b)
    items = []
    for x in root.iter():
        if x.tag.endswith('}Dataflow') and x.get('id'):
            names = [{'lang': n.get('{http://www.w3.org/XML/1998/namespace}lang'), 'text': n.text} for n in x if n.tag.endswith('}Name')]
            if query.casefold() in (x.get('id', '') + ' ' + ' '.join((str(n['text']) for n in names))).casefold():
                items.append({'id': x.get('id'), 'version': x.get('version'), 'names': names})
    return {'source': u, 'count': len(items), 'flows': items}

def identifier(value):
    if not re.fullmatch('[A-Za-z0-9_]{1,80}', value):
        raise ValueError('Invalid identifier')
    return value

def metadata(kind, id):
    if kind not in ['dataflow', 'datastructure', 'codelist', 'conceptscheme']:
        raise ValueError('Invalid type')
    b, u = get('/metadata/' + kind + '/BBK/' + identifier(id), {'references': 'all'})
    return {'source': u, 'xml': b.decode('utf-8-sig')}

def data(flow, key, start, end, limit):
    identifier(flow)
    if not re.fullmatch('[A-Za-z0-9_.+-]{1,250}', key) or '.' not in key:
        raise ValueError('Supply a valid SDMX key')
    if not re.fullmatch('\\d{4}(?:-(?:\\d{2}(?:-\\d{2})?|[QSW]\\d{1,2}))?', start) or not re.fullmatch('\\d{4}(?:-(?:\\d{2}(?:-\\d{2})?|[QSW]\\d{1,2}))?', end):
        raise ValueError('Invalid period')
    if not 1 <= limit <= 1000:
        raise ValueError('limit 1–1000')
    b, u = get('/data/' + flow + '/' + key, {'format': 'sdmx_csv', 'lang': 'en', 'startPeriod': start, 'endPeriod': end})
    rows = list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
    return {'source': u, 'rows_in_response': len(rows), 'returned': min(len(rows), limit), 'truncated': len(rows) > limit, 'rows': rows[:limit], 'note': 'Preserve title, unit and original source; third-party data may have separate reuse restrictions.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    c = s.add_parser('catalog')
    c.add_argument('query', nargs='?', default='')
    m = s.add_parser('metadata')
    m.add_argument('kind', choices=['dataflow', 'datastructure', 'codelist', 'conceptscheme'])
    m.add_argument('id')
    d = s.add_parser('data')
    d.add_argument('flow')
    d.add_argument('key')
    d.add_argument('--start', required=True)
    d.add_argument('--end', required=True)
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = catalog(a.query) if a.command == 'catalog' else metadata(a.kind, a.id) if a.command == 'metadata' else data(a.flow, a.key, a.start, a.end, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
