"""Chile INE SIMEL SDMX dataflow discovery, metadata and bounded series."""
import release_runtime
import argparse, csv, io, json, re, xml.etree.ElementTree as ET
import requests
BASE = 'https://sdmx.ine.gob.cl/rest/'
MAX = 12 * 1024 * 1024

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=40, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX:
                raise ValueError('response exceeds 12 MiB')
            chunks.append(b)
        return (r.url, b''.join(chunks))

def _id(x):
    if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,120}', x) or '..' in x:
        raise ValueError('invalid identifier')
    return x

def _flows(b):
    root = ET.fromstring(b)
    out = []
    for e in root.iter():
        if e.tag.endswith('}Dataflow') and e.get('id'):
            names = {n.get('{http://www.w3.org/XML/1998/namespace}lang', ''): n.text for n in e if n.tag.endswith('}Name')}
            out.append({'id': e.get('id'), 'agency': e.get('agencyID'), 'version': e.get('version'), 'names': names})
    return out

def search(keyword, limit=20):
    if not keyword or len(keyword) > 120 or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    url, b = _get('dataflow')
    q = keyword.casefold()
    items = [x for x in _flows(b) if q in (x['id'] + ' ' + str(x['names'])).casefold()]
    return {'source': url, 'count': len(items), 'results': items[:limit]}

def metadata(flow, version='1.0'):
    url, b = _get('dataflow/CL01/' + _id(flow) + '/' + _id(version), {'references': 'all'})
    return {'source': url, 'structure_xml': b.decode('utf-8-sig')}

def data(flow, key, start, end, version='1.0'):
    _id(flow)
    _id(version)
    _id(key)
    if not re.fullmatch('\\d{4}', str(start)) or not re.fullmatch('\\d{4}', str(end)) or int(start) > int(end) or (int(end) - int(start) > 5):
        raise ValueError('year interval must span at most five years')
    url, b = _get('data/CL01,' + flow + ',' + version + '/' + key, {'format': 'csv', 'startPeriod': start, 'endPeriod': end})
    reader = csv.DictReader(io.StringIO(b.decode('utf-8-sig')))
    if not reader.fieldnames or 'OBS_VALUE' not in reader.fieldnames:
        raise ValueError('invalid SDMX CSV')
    return {'source': url, 'columns': reader.fieldnames, 'rows': list(reader), 'note': '保留观察状态、单位及指标代码，须结合官方元数据解释。'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('metadata')
    a.add_argument('flow')
    a.add_argument('--version', default='1.0')
    a = s.add_parser('data')
    a.add_argument('flow')
    a.add_argument('key')
    a.add_argument('start')
    a.add_argument('end')
    a.add_argument('--version', default='1.0')
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.flow, a.version) if a.cmd == 'metadata' else data(a.flow, a.key, a.start, a.end, a.version)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
