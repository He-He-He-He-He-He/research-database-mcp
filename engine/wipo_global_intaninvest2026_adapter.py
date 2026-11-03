"""Global INTAN-Invest 2026 annual extrapolated estimates used by WIPO/Luiss."""
import release_runtime
import argparse, csv, io, json, re, requests
URL = 'https://global-intaninvest.luiss.it/wp-content/themes/wp-bootstrap-starter-child/download-2026/annual%20extrapolated%20estimates.csv'

def catalog():
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('unexpected data size')
    rows = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    a = list(rows)
    return {'source': URL, 'columns': rows.fieldnames, 'geographies': sorted({x['geo_code'] for x in a}), 'years': sorted({x['year'] for x in a}), 'note': 'Consult provider variable documentation and technical reports before interpreting units.'}

def query(area, start, end, columns=None):
    if not isinstance(area, str) or not re.fullmatch('[A-Z0-9]{2,5}', area) or (not 1995 <= start <= end <= 2100):
        raise ValueError('invalid query')
    columns = columns or ['I_NatAcc', 'I_NonNatAcc']
    if not isinstance(columns, list) or not 1 <= len(columns) <= 50 or any((not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_]{1,50}', x) for x in columns)):
        raise ValueError('invalid columns')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('unexpected data size')
    reader = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    if not {'year', 'geo_code', *columns}.issubset(reader.fieldnames or []):
        raise ValueError('unknown columns or schema')
    rows = [{k: x[k] for k in ('year', 'geo_code', *columns)} for x in reader if x['geo_code'] == area and x['year'].isdigit() and (start <= int(x['year']) <= end)]
    return {'source': URL, 'dataset': 'Global INTAN-Invest July 2026 annual extrapolated estimates', 'records': rows, 'note': 'Research estimates, including assets outside official national-account investment; NA means missing. Verify units and price basis per variable and geography with provider documentation.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('catalog')
    q = s.add_parser('data')
    q.add_argument('area')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    q.add_argument('--columns', nargs='+')
    a = p.parse_args()
    v = catalog() if a.cmd == 'catalog' else query(a.area, a.start, a.end, a.columns)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
