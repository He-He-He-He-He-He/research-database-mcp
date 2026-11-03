"""Thailand National Statistical Office StatHub SDMX discovery and queries."""
import release_runtime
import argparse, csv, io, json, re, urllib.parse, xml.etree.ElementTree as ET
import requests
BASE = 'https://ns2-stathub.nso.go.th/rest'

def get(path, params=None, accept='application/vnd.sdmx.structure+xml;version=2.1'):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, params=params, headers={'Accept': accept}, timeout=40, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for chunk in r.iter_content(65536):
            b.extend(chunk)
            if len(b) > 12000000:
                raise ValueError('Response exceeds 12 MB; select dimensions')
        return (bytes(b), r.url)

def validate(agency, flow, version):
    if not re.fullmatch('[\\w@.-]+', agency) or not re.fullmatch('[\\w@.-]+', flow) or (not re.fullmatch('\\d+(?:\\.\\d+)*', version)):
        raise ValueError('Invalid identifier')

def catalog(keyword=''):
    b, url = get('/dataflow/all/all/latest')
    root = ET.fromstring(b)
    items = []
    for x in root.iter():
        if x.tag.endswith('}Dataflow') and x.get('id'):
            names = [{'lang': z.get('{http://www.w3.org/XML/1998/namespace}lang'), 'name': z.text} for z in x if z.tag.endswith('}Name')]
            if keyword.casefold() in (x.get('id', '') + ' ' + ' '.join((str(z['name']) for z in names))).casefold():
                items.append({'agency': x.get('agencyID'), 'id': x.get('id'), 'version': x.get('version'), 'names': names})
    return {'source': url, 'count': len(items), 'flows': items}

def metadata(agency, flow, version):
    validate(agency, flow, version)
    b, url = get('/dataflow/' + agency + '/' + flow + '/' + version, {'references': 'all'})
    return {'source': url, 'format': 'SDMX XML', 'xml': b.decode('utf-8-sig')}

def data(agency, flow, version, key, start, end, last, limit):
    validate(agency, flow, version)
    if not re.fullmatch('[A-Za-z0-9_+.*-]+', key):
        raise ValueError('Invalid dimension key')
    if not 1 <= limit <= 1000:
        raise ValueError('Limit 1–1000')
    if (start is None) != (end is None):
        raise ValueError('Supply both start and end')
    if start is not None and (not (1800 <= start <= end <= 2700 and end - start <= 10)):
        raise ValueError('Invalid year range')
    params = {'lastNObservations': last} if start is None else {'startPeriod': start, 'endPeriod': end}
    b, url = get('/data/' + agency + ',' + flow + ',' + version + '/' + key, params, 'application/vnd.sdmx.data+csv;labels=both')
    rows = list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
    return {'source': url, 'rows_in_response': len(rows), 'returned': min(limit, len(rows)), 'truncated': len(rows) > limit, 'rows': rows[:limit], 'note': 'Preserve source year and actual source field. Many Thai series use Buddhist Era years; check individual metadata before converting dates.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    c = s.add_parser('catalog')
    c.add_argument('keyword', nargs='?', default='')
    for cmd in ['metadata', 'data']:
        x = s.add_parser(cmd)
        x.add_argument('flow')
        x.add_argument('--agency', default='TNSO')
        x.add_argument('--version', required=True)
        if cmd == 'data':
            x.add_argument('--key', default='all')
            x.add_argument('--start', type=int)
            x.add_argument('--end', type=int)
            x.add_argument('--last', type=int, default=1, choices=range(1, 6))
            x.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    res = catalog(a.keyword) if a.command == 'catalog' else metadata(a.agency, a.flow, a.version) if a.command == 'metadata' else data(a.agency, a.flow, a.version, a.key, a.start, a.end, a.last, a.limit)
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
