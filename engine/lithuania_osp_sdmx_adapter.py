"""Lithuania State Data Agency OSP SDMX catalogue, structure and data."""
import release_runtime
import argparse, json, re, xml.etree.ElementTree as ET
import requests
BASE = 'https://osp-rs.stat.gov.lt/'
MAX = 12 * 1024 * 1024

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=45, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX:
                raise ValueError('response exceeds 12 MiB')
            parts.append(b)
        return (r.url, b''.join(parts))

def _id(x):
    if not re.fullmatch('[A-Za-z0-9_]{1,100}', x):
        raise ValueError('invalid id')
    return x

def _flows(b):
    root = ET.fromstring(b)
    out = []
    for e in root.iter():
        if e.tag.endswith('}Dataflow') and e.get('id'):
            names = {n.get('{http://www.w3.org/XML/1998/namespace}lang', ''): n.text for n in e if n.tag.endswith('}Name')}
            out.append({'id': e.get('id'), 'agency': e.get('agencyID'), 'names': names})
    return out

def search(keyword, limit=20):
    if not keyword or len(keyword) > 120 or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    url, b = _get('rest_xml/dataflow/')
    q = keyword.casefold()
    items = [x for x in _flows(b) if q in (x['id'] + ' ' + str(x['names'])).casefold()]
    return {'source': url, 'count': len(items), 'results': items[:limit]}

def metadata(flow):
    url, b = _get('rest_xml/dataflow/LSD/' + _id(flow))
    root = ET.fromstring(b)
    r = next((x for x in root.iter() if x.tag.split('}')[-1] == 'Ref' and x.get('class') == 'DataStructure'), None)
    if r is None:
        raise ValueError('missing data structure reference')
    durl, db = _get('rest_xml/datastructure/LSD/' + _id(r.get('id')))
    return {'source': url, 'flow': _flows(b), 'structure_source': durl, 'structure_xml': db.decode('utf-8')}

def data(flow, start, end):
    for x in (start, end):
        if not re.fullmatch('\\d{4}(-\\d{2}|-Q[1-4]|-S[12])?', x):
            raise ValueError('invalid period')
    if start > end or int(end[:4]) - int(start[:4]) > 1:
        raise ValueError('choose at most a one-year span')
    url, b = _get('rest_json/data/' + _id(flow) + '/', {'startPeriod': start, 'endPeriod': end})
    d = json.loads(b)
    if 'dataSets' not in d or 'structure' not in d:
        raise ValueError('invalid SDMX JSON')
    return {'source': url, 'result': d, 'note': '上游不支持其他维度服务端过滤，完整保留范围内各观察和维度。'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('metadata')
    a.add_argument('flow')
    a = s.add_parser('data')
    a.add_argument('flow')
    a.add_argument('start')
    a.add_argument('end')
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.flow) if a.cmd == 'metadata' else data(a.flow, a.start, a.end)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
