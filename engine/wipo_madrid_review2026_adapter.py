"""WIPO Madrid Yearly Review 2026 source workbooks."""
import release_runtime
import argparse, datetime, io, json, re, openpyxl, requests
BASE = 'https://www.wipo.int/edocs/pubdocs/en/wipo-pub-940-2026-tech'

def _open(part, local_file):
    if part not in (1, 2, 3):
        raise ValueError('invalid workbook part')
    if local_file:
        return openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    r = requests.get(BASE + str(part) + '.xlsx', timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected workbook size')
    return openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)

def catalog(part, local_file=None):
    w = _open(part, local_file)
    try:
        return {'source': local_file if local_file else BASE + str(part) + '.xlsx', 'report': None if local_file else 'Madrid Yearly Review 2026', 'note': 'Local workbook provenance and version are unverified.' if local_file else 'Official source workbook may be updated.', 'tables': [{'id': s.title, 'title': ' '.join((str(x) for row in s.iter_rows(max_row=2, values_only=True) for x in row if x is not None))} for s in w]}
    finally:
        w.close()

def rows(part, table, keyword='', limit=100, local_file=None):
    if not isinstance(table, str) or not re.fullmatch('[A-Za-z0-9_-]{1,50}', table) or (not isinstance(keyword, str)) or (len(keyword) > 150) or (not 1 <= limit <= 1000):
        raise ValueError('invalid query')
    w = _open(part, local_file)
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
            if i <= 10:
                context.append({'row': i, 'cells': vals})
            if not vals or (keyword and keyword.casefold() not in ' '.join((str(x) for x in vals if x is not None)).casefold()):
                continue
            count += 1
            if len(out) < limit:
                out.append({'row': i, 'cells': vals})
        return {'source': local_file if local_file else BASE + str(part) + '.xlsx', 'report': None if local_file else 'WIPO Madrid Yearly Review 2026', 'part': part, 'table': table, 'header_context': context, 'matched_count': count, 'records': out, 'note': 'Raw table context and notes preserved; 2025 application counts may be estimates. Applications and registrations are distinct.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('part', type=int, choices=[1, 2, 3])
    c.add_argument('--local-file')
    q = s.add_parser('rows')
    q.add_argument('part', type=int, choices=[1, 2, 3])
    q.add_argument('table')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q.add_argument('--local-file')
    a = p.parse_args()
    v = catalog(a.part, a.local_file) if a.cmd == 'catalog' else rows(a.part, a.table, a.keyword, a.limit, a.local_file)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
