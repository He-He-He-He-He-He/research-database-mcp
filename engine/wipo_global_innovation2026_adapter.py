"""WIPO Global Innovation Index 2026 official database."""
import release_runtime
import argparse, datetime, io, json, re, openpyxl, requests
URL = 'https://www.wipo.int/edocs/pubdocs/en/wipo-pub-2000-2026-tech1.xlsx'

def _open(local_file):
    if local_file:
        return openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected workbook size')
    return openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)

def _rows(sheet):
    it = sheet.values
    headers = next(it)
    for row in it:
        yield {str(k): v.isoformat() if isinstance(v, (datetime.datetime, datetime.date)) else v for k, v in zip(headers, row) if k is not None}

def catalog(kind='indicators', keyword='', limit=100, local_file=None):
    if kind not in ('indicators', 'economies') or not isinstance(keyword, str) or len(keyword) > 100 or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    w = _open(local_file)
    try:
        sheet = w['Index Structure' if kind == 'indicators' else 'Economies']
        rows = [x for x in _rows(sheet) if keyword.casefold() in ' '.join((str(v) for v in x.values() if v is not None)).casefold()]
        return {'source': local_file if local_file else URL, 'kind': kind, 'matched_count': len(rows), 'limit': limit, 'truncated': len(rows) > limit, 'records': rows[:limit], 'note': 'Local workbook provenance and version are unverified.' if local_file else 'Official source workbook may be updated.'}
    finally:
        w.close()

def query(country, keyword='', limit=100, local_file=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or (not isinstance(keyword, str)) or (len(keyword) > 100) or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    w = _open(local_file)
    try:
        sheet = w['Data']
        it = _rows(sheet)
        rows = []
        count = 0
        for d in it:
            if d.get('ISO3') != country or keyword.casefold() not in (str(d.get('NUM', '')) + ' ' + str(d.get('NAME', ''))).casefold():
                continue
            count += 1
            if len(rows) < limit:
                rows.append(d)
        return {'source': local_file if local_file else URL, 'provider': None if local_file else 'WIPO Global Innovation Index 2026', 'matched_count': count, 'limit': limit, 'truncated': count > limit, 'records': rows, 'note': 'If truncated is true increase limit (maximum 500) or narrow keyword; this is local truncation, not pagination. Report year 2026; underlying indicator years vary. SCORE and RANK are distinct from raw VALUE_SCREEN; check data year and methodology.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['indicators', 'economies'])
    c.add_argument('--keyword', default='')
    c.add_argument('--limit', type=int, default=100)
    c.add_argument('--local-file')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q.add_argument('--local-file')
    a = p.parse_args()
    v = catalog(a.kind, a.keyword, a.limit, a.local_file) if a.cmd == 'catalog' else query(a.country, a.keyword, a.limit, a.local_file)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
