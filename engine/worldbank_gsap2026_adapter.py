"""World Bank GSAP September 2026 vintage subnational lined-up poverty estimates."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0042041/DR0052555/AM26%20-%20GSAP%20data.xlsx'
YEARS = (2010, 2019, 2021, 2023, 2024)

def _workbook(local_file):
    if local_file:
        return openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected file size')
    return openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)

def dictionary(local_file=None):
    w = _workbook(local_file)
    try:
        it = w['Dictionary'].values
        h = next(it)
        return {'source': local_file if local_file else URL, 'records': [dict(zip(h, row)) for row in it], 'note': 'Local workbook provenance and version are unverified.' if local_file else 'Official source workbook; source may be updated.'}
    finally:
        w.close()

def query(country, year=2024, area='', limit=100, local_file=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or year not in YEARS or (not isinstance(area, str)) or (len(area) > 100) or (not 1 <= limit <= 1000):
        raise ValueError('invalid query')
    w = _workbook(local_file)
    try:
        it = w['Data ' + str(year)].values
        h = next(it)
        if not {'code', 'baseyear', 'lineupyear', 'sample', 'poor300_ln', 'poor420_ln', 'poor830_ln'}.issubset(h):
            raise ValueError('unexpected workbook schema')
        data = []
        count = 0
        for row in it:
            d = dict(zip(h, row))
            if d['code'] != country or (area and area.casefold() not in str(d['sample']).casefold()):
                continue
            count += 1
            if len(data) < limit:
                data.append(d)
        return {'source': local_file if local_file else URL, 'vintage': None if local_file else 'Fall 2026', 'matched_count': count, 'records': data, 'note': 'Modelled lined-up estimates, not direct survey observations; poverty columns are proportions 0–1.' + (' Local workbook provenance and version are unverified.' if local_file else ' Official source may be updated.')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('dictionary')
    d.add_argument('--local-file')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('--year', type=int, choices=YEARS, default=2024)
    q.add_argument('--area', default='')
    q.add_argument('--limit', type=int, default=100)
    q.add_argument('--local-file')
    a = p.parse_args()
    v = dictionary(a.local_file) if a.cmd == 'dictionary' else query(a.country, a.year, a.area, a.limit, a.local_file)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
