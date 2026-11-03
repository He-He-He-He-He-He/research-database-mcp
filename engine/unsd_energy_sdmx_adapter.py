"""UN Statistics Division energy statistics, SDMX code lists and annual data."""
import release_runtime
import argparse, csv, io, json, re, xml.etree.ElementTree as ET
import requests
BASE = 'https://data.un.org/WS/rest/'
MAX = 10 * 1024 * 1024

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        pieces = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > MAX:
                raise ValueError('response exceeds 10 MiB')
            pieces.append(b)
        return (r.url, b''.join(pieces))

def codes(kind, keyword='', limit=50):
    kinds = {'area': 'CL_AREA_NRG', 'commodity': 'CL_COMMODITY_NRG', 'transaction': 'CL_TRANSACTION_NRG', 'unit': 'CL_UNIT_MEASURE_NRG'}
    if kind not in kinds or not 1 <= limit <= 100 or len(keyword) > 100:
        raise ValueError('invalid code search')
    url, b = _get('datastructure/UNSD/DSD_Energy/', {'references': 'all'})
    root = ET.fromstring(b)
    out = []
    for cl in root.iter():
        if cl.tag.endswith('}Codelist') and cl.get('id') == kinds[kind]:
            for c in cl:
                if not c.tag.endswith('}Code'):
                    continue
                names = {x.get('{http://www.w3.org/XML/1998/namespace}lang', ''): x.text for x in c if x.tag.endswith('}Name')}
                if keyword.casefold() in (c.get('id', '') + ' ' + str(names)).casefold():
                    out.append({'code': c.get('id'), 'names': names})
    return {'source': url, 'count': len(out), 'results': out[:limit]}

def data(area, commodity, transaction, start, end):
    if not re.fullmatch('\\d{3}', area) or any((not re.fullmatch('[A-Za-z0-9_]{1,20}', x) for x in (commodity, transaction))) or (not 1900 <= int(start) <= int(end) <= 2100) or (int(end) - int(start) > 30):
        raise ValueError('invalid dimensions or year range')
    url, b = _get('data/UNSD,DF_UNDATA_ENERGY,/A.' + area + '.' + commodity + '.' + transaction + '/', {'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    reader = csv.DictReader(io.StringIO(b.decode('utf-8-sig')))
    if not reader.fieldnames or 'OBS_VALUE' not in reader.fieldnames:
        raise ValueError('unexpected response')
    return {'source': url, 'rows': list(reader), 'note': 'Preserve UNIT_MEASURE, UNIT_MULT and OBS_STATUS; do not assume all values are observed.'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('codes')
    a.add_argument('kind', choices=['area', 'commodity', 'transaction', 'unit'])
    a.add_argument('keyword', nargs='?', default='')
    a.add_argument('--limit', type=int, default=50)
    a = s.add_parser('data')
    a.add_argument('area')
    a.add_argument('commodity')
    a.add_argument('transaction')
    a.add_argument('start')
    a.add_argument('end')
    a = p.parse_args()
    x = codes(a.kind, a.keyword, a.limit) if a.cmd == 'codes' else data(a.area, a.commodity, a.transaction, a.start, a.end)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
