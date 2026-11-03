"""Italy ISTAT official SDMX v2.1, with conservative cross-process rate limit."""
import release_runtime
import argparse, fcntl, json, re, time, xml.etree.ElementTree as ET
import requests
ROOT = 'https://esploradati.istat.it/SDMXWS/rest/'
LOCK = '/tmp/research-toolkit-istat-sdmx.lock'

def _get(path, params=None):
    with open(LOCK, 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            lock.seek(0)
            s = lock.read().strip()
            try:
                last = float(s)
            except ValueError:
                last = 0
            wait = 17 - (time.time() - last)
            if wait > 0:
                time.sleep(min(wait, 17))
            lock.seek(0)
            lock.truncate()
            lock.write(str(time.time()))
            lock.flush()
            with requests.get(ROOT + path, params=params, timeout=60, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
                r.raise_for_status()
                parts = []
                size = 0
                for b in r.iter_content(65536):
                    size += len(b)
                    if size > 20 * 1024 * 1024:
                        raise ValueError('response exceeds 20 MiB')
                    parts.append(b)
                return {'source': r.url, 'xml': b''.join(parts)}
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)

def _flow(flow):
    if not re.fullmatch('[A-Za-z0-9_]{1,100}', flow):
        raise ValueError('invalid flow ID')
    return flow

def search(keyword, limit=20):
    if not keyword or len(keyword) > 150 or (not 1 <= limit <= 100):
        raise ValueError('invalid search')
    r = _get('dataflow/IT1/all/latest')
    root = ET.fromstring(r['xml'])
    out = []
    count = 0
    lang = '{http://www.w3.org/XML/1998/namespace}lang'
    for e in root.iter():
        if e.tag.rsplit('}', 1)[-1] != 'Dataflow':
            continue
        names = {x.get(lang, ''): x.text for x in e if x.tag.rsplit('}', 1)[-1] == 'Name'}
        if keyword.casefold() not in ' '.join((str(x or '') for x in names.values())).casefold():
            continue
        count += 1
        if len(out) < limit:
            out.append({'id': e.get('id'), 'agency': e.get('agencyID'), 'version': e.get('version'), 'names': names})
    return {'source': r['source'], 'total': count, 'dataflows': out}

def structure(flow):
    r = _get('dataflow/IT1/' + _flow(flow) + '/1.0', {'references': 'all'})
    ET.fromstring(r['xml'])
    return {'source': r['source'], 'sdmx_xml': r['xml'].decode('utf-8-sig')}

def data(flow, key, start, end):
    flow = _flow(flow)
    if not re.fullmatch('[A-Za-z0-9_+-]+(?:\\.[A-Za-z0-9_+-]+){0,15}', key) or len(key) > 300:
        raise ValueError('use bounded nonempty dimension codes')
    if not re.fullmatch('\\d{4}(?:-(?:0[1-9]|1[0-2]))?', start) or not re.fullmatch('\\d{4}(?:-(?:0[1-9]|1[0-2]))?', end) or start > end:
        raise ValueError('invalid time period')
    r = _get('data/IT1,' + flow + ',1.0/' + key, {'startPeriod': start, 'endPeriod': end})
    root = ET.fromstring(r['xml'])
    output = []
    for series in root.iter():
        if series.tag.rsplit('}', 1)[-1] != 'Series':
            continue
        row = {'dimensions': {}, 'attributes': {}, 'observations': []}
        for part in series:
            typ = part.tag.rsplit('}', 1)[-1]
            if typ in ('SeriesKey', 'Attributes'):
                target = row['dimensions' if typ == 'SeriesKey' else 'attributes']
                target.update({e.get('id'): e.get('value') for e in part if e.get('id')})
            elif typ == 'Obs':
                record = {}
                for e in part:
                    name = e.tag.rsplit('}', 1)[-1]
                    if name == 'ObsDimension':
                        record['period'] = e.get('value')
                    elif name == 'ObsValue':
                        record['value'] = e.get('value')
                    elif name == 'Attributes':
                        record['attributes'] = {x.get('id'): x.get('value') for x in e if x.get('id')}
                row['observations'].append(record)
        output.append(row)
    return {'source': r['source'], 'series': output, 'note': 'Codes, units, scale and status must be resolved against flow metadata; preserve revision indicators.'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('structure')
    a.add_argument('flow')
    a = s.add_parser('data')
    a.add_argument('flow')
    a.add_argument('key')
    a.add_argument('start')
    a.add_argument('end')
    a = p.parse_args()
    d = search(a.keyword, a.limit) if a.cmd == 'search' else structure(a.flow) if a.cmd == 'structure' else data(a.flow, a.key, a.start, a.end)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
