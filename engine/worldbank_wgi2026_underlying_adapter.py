"""World Bank WGI 2026 underlying source indicators, 1996–2025."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0038026/DR0095946/Raw%20Data%20from%20Underlying%20Data%20Sources%20%281996-2025%29.xlsx'
SHEETS = ('va', 'pv', 'ge', 'rq', 'rl', 'cc')

def query(country, dimension, start=2025, end=2025, keyword='', limit=100, local_file=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or dimension not in SHEETS or (not 1996 <= start <= end <= 2025) or (not isinstance(keyword, str)) or (len(keyword) > 120) or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        r = requests.get(URL, timeout=120)
        r.raise_for_status()
        if len(r.content) > 40000000:
            raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w[dimension].values
        h = next(it)
        if not {'DataSourceCode', 'Organization', 'DataSource', 'indicator', 'econ_code', 'production_year', 'value', 'minimum', 'maximum', 'orientation'}.issubset(h):
            raise ValueError('unexpected schema')
        count = 0
        rows = []
        for row in it:
            d = dict(zip(h, row))
            year = d['production_year']
            if d['econ_code'] != country or not isinstance(year, int) or (not start <= year <= end) or (keyword.casefold() not in (str(d['indicator']) + ' ' + str(d['DataSource'])).casefold()):
                continue
            count += 1
            if len(rows) < limit:
                rows.append(d)
        return {'source': local_file if local_file else URL, 'dataset': None if local_file else 'WGI 2026 underlying source data', 'dimension': dimension, 'matched_count': count, 'records': rows, 'note': 'Raw heterogeneous source series; production year may differ from fieldwork year. Original value ranges, orientation and source rights vary; do not equate with WGI aggregate.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('dimension', choices=SHEETS)
    p.add_argument('--start', type=int, default=2025)
    p.add_argument('--end', type=int, default=2025)
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.dimension, a.start, a.end, a.keyword, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
