"""World Bank Subnational Multidimensional Poverty Measure, September 2026."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0064796/DR0092190/AM26%20-%20Subnational%20MPM.xlsx'

def _workbook(local_file):
    if local_file:
        return openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    if len(r.content) > 30000000:
        raise ValueError('unexpected file size')
    return openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)

def dictionary(local_file=None):
    w = _workbook(local_file)
    try:
        it = w['Dictionary'].values
        h = next(it)
        return {'source': local_file if local_file else URL, 'records': [dict(zip(h, row)) for row in it], 'note': 'Local workbook provenance and version are unverified.' if local_file else 'Official source workbook may be updated.'}
    finally:
        w.close()

def query(country, year=None, area='', limit=20, local_file=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or (year is not None and (not 1900 <= year <= 2100)) or (not isinstance(area, str)) or (len(area) > 120) or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    w = _workbook(local_file)
    try:
        it = w['Data'].values
        h = next(it)
        if not {'code', 'year', 'sample', 'mdpoor_i1', 'dep_poor1'}.issubset(h):
            raise ValueError('unexpected workbook schema')
        out = []
        count = 0
        for row in it:
            d = dict(zip(h, row))
            if d['code'] != country or (year is not None and d['year'] != year) or (area and area.casefold() not in str(d['sample']).casefold()):
                continue
            count += 1
            if len(out) < limit:
                out.append(d)
        return {'source': local_file if local_file else URL, 'vintage': None if local_file else 'Fall 2026', 'matched_count': count, 'records': out, 'note': 'Values remain raw: consult dictionary for scale, welfare type, survey coverage, year, and comparability.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('dictionary')
    d.add_argument('--local-file')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('--year', type=int)
    q.add_argument('--area', default='')
    q.add_argument('--limit', type=int, default=20)
    q.add_argument('--local-file')
    a = p.parse_args()
    v = dictionary(a.local_file) if a.cmd == 'dictionary' else query(a.country, a.year, a.area, a.limit, a.local_file)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
