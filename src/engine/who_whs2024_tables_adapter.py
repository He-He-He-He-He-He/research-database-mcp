"""WHO World Health Statistics 2024 official country and global workbook."""
import release_runtime
import argparse
import io
import json
import re
import openpyxl
import requests
URL = 'https://cdn.who.int/media/docs/default-source/gho-documents/world-health-statistic-reports/2024/web_download.xlsx?sfvrsn=4e7bbebd_1'
DOCUMENT = 'https://www.who.int/data/gho/publications/world-health-statistics'
MAX_BYTES = 2000000
EXPECTED = ['IND_NAME', 'DIM_GEO_NAME', 'IND_CODE', 'DIM_GEO_CODE', 'DIM_TIME_YEAR', 'DIM_1_CODE', 'VALUE_NUMERIC', 'VALUE_STRING', 'VALUE_COMMENTS']

def _book():
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for block in r.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    if not {'readme', 'data'}.issubset(w.sheetnames):
        w.close()
        raise ValueError('unexpected workbook sheets')
    return w

def _rows(book):
    rows = book['data'].values
    header = list(next(rows))
    if header != EXPECTED:
        raise ValueError('unexpected workbook columns')
    return rows

def indicators(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 150 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 500):
        raise ValueError('invalid keyword or limit')
    w = _book()
    try:
        unique = set()
        for r in _rows(w):
            name, code = (r[0], r[2])
            if isinstance(name, str) and isinstance(code, str) and (keyword.casefold() in (name + ' ' + code).casefold()):
                unique.add((code, name))
        x = sorted(unique)
        return {'source': URL, 'publication': DOCUMENT, 'report_published': '2024-05-21', 'workbook_readme': w['readme']['A1'].value, 'matched_count': len(x), 'returned': min(limit, len(x)), 'indicators': [{'code': a, 'name': b} for a, b in x[:limit]]}
    finally:
        w.close()

def data(geo, indicator, limit=100):
    if not isinstance(geo, str) or not re.fullmatch('[A-Z0-9_]{2,30}', geo):
        raise ValueError('invalid geographic code')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', indicator):
        raise ValueError('invalid indicator code')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('invalid limit')
    w = _book()
    try:
        out = []
        count = 0
        for r in _rows(w):
            if r[2] != indicator or r[3] != geo:
                continue
            count += 1
            if len(out) < limit:
                out.append(dict(zip(EXPECTED, r)))
        return {'source': URL, 'publication': DOCUMENT, 'report_published': '2024-05-21', 'workbook_readme': w['readme']['A1'].value, 'geo': geo, 'indicator': indicator, 'matched_count': count, 'returned': len(out), 'records': out, 'note': 'Original numeric and display values, dimensions, year, and comments are retained. Values may be estimates, survey windows can differ from row year, and missing is not zero. Current workbook may be changed; verify strict historical values with the 2024 report.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('indicators')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q = s.add_parser('data')
    q.add_argument('geo')
    q.add_argument('indicator')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    x = indicators(a.keyword, a.limit) if a.command == 'indicators' else data(a.geo, a.indicator, a.limit)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
