"""Swiss FSO Swiss Stats Explorer SDMX public data."""
import release_runtime
import argparse, csv, io, json, re, xml.etree.ElementTree as ET
import requests
ROOT = 'https://disseminate.stats.swiss/rest/'

def _get(path, params=None, accept=None):
    with requests.get(ROOT + path, params=params, timeout=40, stream=True, headers={'Accept': accept or 'application/vnd.sdmx.structure+xml;version=2.1', 'Accept-Language': 'en', 'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(b)
        return {'source': r.url, 'bytes': b''.join(parts)}

def _id(agency, flow, version):
    if not re.fullmatch('[A-Z0-9_.]{2,50}', agency) or not re.fullmatch('[A-Z0-9_]{2,100}', flow) or (not re.fullmatch('\\d+(?:\\.\\d+){0,2}', version)):
        raise ValueError('invalid agency, flow or version')

def search(keyword, limit=20):
    if not keyword or len(keyword) > 150 or (not 1 <= limit <= 100):
        raise ValueError('invalid search')
    r = _get('dataflow/all/all/latest')
    root = ET.fromstring(r['bytes'])
    lang = '{http://www.w3.org/XML/1998/namespace}lang'
    rows = []
    count = 0
    for e in root.iter():
        if e.tag.rsplit('}', 1)[-1] != 'Dataflow':
            continue
        names = {x.get(lang, ''): x.text for x in e if x.tag.rsplit('}', 1)[-1] == 'Name'}
        if keyword.casefold() not in ' '.join((str(x or '') for x in names.values())).casefold():
            continue
        count += 1
        if len(rows) < limit:
            rows.append({'agency': e.get('agencyID'), 'id': e.get('id'), 'version': e.get('version'), 'names': names})
    return {'source': r['source'], 'total': count, 'dataflows': rows}

def structure(agency, flow, version):
    _id(agency, flow, version)
    r = _get(f'dataflow/{agency}/{flow}/{version}', {'references': 'all', 'detail': 'referencepartial'})
    ET.fromstring(r['bytes'])
    return {'source': r['source'], 'sdmx_xml': r['bytes'].decode('utf-8-sig')}

def data(agency, flow, version, key, start, end, limit=200):
    _id(agency, flow, version)
    if not re.fullmatch('[A-Za-z0-9_+-]+(?:\\.[A-Za-z0-9_+-]+){0,15}', key) or len(key) > 300:
        raise ValueError('use bounded nonempty dimension values')
    if not re.fullmatch('\\d{4}(?:-(?:0[1-9]|1[0-2]))?', start) or not re.fullmatch('\\d{4}(?:-(?:0[1-9]|1[0-2]))?', end) or start > end or (not 1 <= limit <= 1000):
        raise ValueError('invalid period or limit')
    path = f'data/{agency},{flow},{version}/{key}'
    r = _get(path, {'startPeriod': start, 'endPeriod': end, 'dimensionAtObservation': 'AllDimensions'}, 'text/csv')
    reader = csv.DictReader(io.StringIO(r['bytes'].decode('utf-8-sig')))
    if not reader.fieldnames or 'OBS_VALUE' not in reader.fieldnames:
        raise ValueError('unexpected SDMX CSV')
    rows = []
    total = 0
    for row in reader:
        total += 1
        if len(rows) < limit:
            rows.append(row)
    return {'source': r['source'], 'columns': reader.fieldnames, 'total': total, 'observations': rows, 'note': 'Preserve UNIT, MULT, status and other dimensions; consult structural metadata.'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('structure')
    a.add_argument('agency')
    a.add_argument('flow')
    a.add_argument('version')
    a = s.add_parser('data')
    a.add_argument('agency')
    a.add_argument('flow')
    a.add_argument('version')
    a.add_argument('key')
    a.add_argument('start')
    a.add_argument('end')
    a.add_argument('--limit', type=int, default=200)
    a = p.parse_args()
    d = search(a.keyword, a.limit) if a.cmd == 'search' else structure(a.agency, a.flow, a.version) if a.cmd == 'structure' else data(a.agency, a.flow, a.version, a.key, a.start, a.end, a.limit)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
