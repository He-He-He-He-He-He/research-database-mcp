"""World Bank Global Financial Development Database November 2021 workbook."""
import release_runtime
import argparse
import io
import json
import re
import requests
import openpyxl
URL = 'https://thedocs.worldbank.org/en/doc/92631f5aa8ecaed440d9b2e0ab8810e7-0050062021/original/Global-Financial-Development-Database-11-1-2021.xlsx'
DOCUMENT = 'https://www.worldbank.org/en/publication/gfdr/data/global-financial-development-database'
MAX_BYTES = 15000000

def _book():
    with requests.get(URL, timeout=45, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    if not {'Data - November 2021', 'Definitions & Sources'}.issubset(w.sheetnames):
        w.close()
        raise ValueError('unexpected workbook')
    return w

def _definitions(w):
    rows = w['Definitions & Sources'].values
    header = next(rows)
    return [dict(zip(header[:8], r[:8])) for r in rows if isinstance(r[1], str) and r[1].startswith('GFDD.')]

def indicators(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 150 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 500):
        raise ValueError('invalid keyword or limit')
    w = _book()
    try:
        out = [x for x in _definitions(w) if keyword.casefold() in (str(x['Indicator Code']) + ' ' + str(x['Indicator Name'])).casefold()]
        return {'source': URL, 'documentation': DOCUMENT, 'edition': 'November 2021', 'matched_count': len(out), 'returned': min(len(out), limit), 'indicators': out[:limit], 'note': 'Names, definitions, coverage and original compilation sources are retained; source institutions differ by indicator.'}
    finally:
        w.close()

def data(iso3, column, start=1960, end=2021, limit=100):
    if not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3):
        raise ValueError('invalid ISO3')
    if not isinstance(column, str) or not re.fullmatch('[a-z0-9_]{1,40}', column):
        raise ValueError('invalid Data sheet column')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (start, end, limit))) or not 1960 <= start <= end <= 2021 or (not 1 <= limit <= 500):
        raise ValueError('invalid year or limit')
    w = _book()
    try:
        rows = w['Data - November 2021'].values
        header = list(next(rows))
        if header[:7] != ['iso3', 'iso2', 'imfn', 'country', 'region', 'income', 'year'] or column not in header:
            raise ValueError('unknown column or changed schema')
        ci = header.index(column)
        out = []
        count = 0
        for row in rows:
            if row[0] != iso3 or not isinstance(row[6], int) or (not start <= row[6] <= end):
                continue
            count += 1
            if len(out) < limit:
                out.append({'iso3': row[0], 'iso2': row[1], 'imf_code': row[2], 'country': row[3], 'region': row[4], 'income_group': row[5], 'year': row[6], 'raw_value': row[ci]})
        matches = [x for x in _definitions(w) if ''.join(x['Indicator Code'].split('.')[1:]).lower() == column]
        return {'source': URL, 'documentation': DOCUMENT, 'edition': 'November 2021', 'data_column': column, 'indicator_metadata': matches, 'matched_count': count, 'returned': len(out), 'records': out, 'note': 'November 2021 workbook edition, exact publication day not established. Preserve null, year and indicator-specific source/units; later revisions may differ.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('indicators')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q = s.add_parser('data')
    q.add_argument('iso3')
    q.add_argument('column')
    q.add_argument('--start', type=int, default=1960)
    q.add_argument('--end', type=int, default=2021)
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    out = indicators(a.keyword, a.limit) if a.cmd == 'indicators' else data(a.iso3, a.column, a.start, a.end, a.limit)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
