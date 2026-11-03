"""Luxembourg STATEC LUSTAT SDMX: discover flows, inspect XML, query CSV."""
import release_runtime
import argparse, csv, io, json, re, urllib.parse, xml.etree.ElementTree as ET
import requests
BASE = 'https://lustat.statec.lu/rest'
MAX_BYTES = 12000000

def fetch(path, params=None, accept='application/vnd.sdmx.structure+xml;version=2.1'):
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    session = requests.Session()
    session.trust_env = False
    with session.get(url, headers={'Accept': accept, 'User-Agent': 'ResearchToolkit/1.0'}, timeout=40, stream=True) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            if len(content) > MAX_BYTES:
                raise ValueError('Response exceeds 12 MB; narrow the request.')
        return (bytes(content), url)

def validate(flow, version):
    if not re.fullmatch('[A-Za-z0-9_@.-]+', flow):
        raise ValueError('Invalid dataflow identifier')
    if not re.fullmatch('\\d+(?:\\.\\d+)*', version):
        raise ValueError('Invalid version')

def catalog(query):
    content, url = fetch('/dataflow/LU1/all/latest')
    root = ET.fromstring(content)
    result = []
    for el in root.iter():
        if el.tag.endswith('}Dataflow') and el.get('id'):
            names = [{'language': x.get('{http://www.w3.org/XML/1998/namespace}lang'), 'name': x.text} for x in el if x.tag.endswith('}Name')]
            if query.lower() in (el.get('id', '') + ' ' + ' '.join((n['name'] or '' for n in names))).lower():
                result.append({'id': el.get('id'), 'version': el.get('version'), 'names': names})
    return {'source': url, 'count': len(result), 'flows': result}

def metadata(flow, version):
    validate(flow, version)
    body, url = fetch('/dataflow/LU1/' + urllib.parse.quote(flow, safe='@') + '/' + version, {'references': 'all'})
    return {'source': url, 'format': 'SDMX 2.1 XML', 'xml': body.decode('utf-8-sig')}

def data(flow, version, key, start, end, limit):
    validate(flow, version)
    if not re.fullmatch('[A-Za-z0-9_+.*-]+', key):
        raise ValueError('Invalid SDMX dimension key')
    if not (1900 <= start <= end <= 2100 and end - start <= 10):
        raise ValueError('Use a year range within 1900–2100, at most 11 years')
    if not 1 <= limit <= 1000:
        raise ValueError('Limit must be 1–1000')
    content, url = fetch('/data/LU1,' + urllib.parse.quote(flow, safe='@') + ',' + version + '/' + key, {'startPeriod': start, 'endPeriod': end}, 'application/vnd.sdmx.data+csv;urn=true;file=true;labels=both')
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    rows = list(reader)
    return {'source': url, 'count_returned': min(len(rows), limit), 'rows_in_response': len(rows), 'truncated': len(rows) > limit, 'rows': rows[:limit], 'note': 'Values, labels and notes are returned as published; consult metadata for definitions and units.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('catalog')
    c.add_argument('query', nargs='?', default='')
    m = sub.add_parser('metadata')
    m.add_argument('flow')
    m.add_argument('--version', required=True)
    d = sub.add_parser('data')
    d.add_argument('flow')
    d.add_argument('--version', required=True)
    d.add_argument('--key', default='all')
    d.add_argument('--start', type=int, required=True)
    d.add_argument('--end', type=int, required=True)
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = catalog(a.query) if a.command == 'catalog' else metadata(a.flow, a.version) if a.command == 'metadata' else data(a.flow, a.version, a.key, a.start, a.end, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
