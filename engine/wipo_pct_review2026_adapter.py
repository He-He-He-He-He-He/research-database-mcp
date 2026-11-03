"""WIPO PCT Yearly Review 2026 official tabular source workbook."""
import release_runtime
import argparse, datetime, io, json, re, openpyxl, requests
URL = 'https://www.wipo.int/edocs/pubdocs/en/wipo-pub-901-2026-tech1.xlsx'

def _open(local_file):
    if local_file:
        return openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected workbook size')
    return openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)

def catalog(local_file=None):
    w = _open(local_file)
    try:
        return {'source': local_file if local_file else URL, 'report': None if local_file else 'PCT Yearly Review 2026', 'note': 'Local workbook provenance and version are unverified.' if local_file else 'Official source workbook may be updated.', 'tables': [{'id': s.title, 'title': ' '.join((str(x) for row in s.iter_rows(max_row=2, values_only=True) for x in row if x is not None))} for s in w]}
    finally:
        w.close()

def rows(table, keyword='', limit=100, local_file=None):
    if not isinstance(table, str) or not re.fullmatch('[ABC]\\d{2}', table) or (not isinstance(keyword, str)) or (len(keyword) > 150) or (not 1 <= limit <= 1000):
        raise ValueError('invalid query')
    w = _open(local_file)
    try:
        if table not in w.sheetnames:
            raise ValueError('table not found')
        s = w[table]
        out = []
        context = []
        count = 0
        for i, row in enumerate(s.values, 1):
            vals = [v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v for v in row]
            while vals and vals[-1] is None:
                vals.pop()
            if i <= 9:
                context.append({'row': i, 'cells': vals})
            if not vals or (keyword and keyword.casefold() not in ' '.join((str(x) for x in vals if x is not None)).casefold()):
                continue
            count += 1
            if len(out) < limit:
                out.append({'row': i, 'cells': vals})
        return {'source': local_file if local_file else URL, 'report': None if local_file else 'WIPO PCT Yearly Review 2026', 'table': table, 'header_context': context, 'matched_count': count, 'records': out, 'note': 'Raw table layout and footnotes are preserved; 2025 application figures may be estimates and filing differs from grant.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('--local-file')
    q = s.add_parser('rows')
    q.add_argument('table')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q.add_argument('--local-file')
    a = p.parse_args()
    v = catalog(a.local_file) if a.cmd == 'catalog' else rows(a.table, a.keyword, a.limit, a.local_file)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
