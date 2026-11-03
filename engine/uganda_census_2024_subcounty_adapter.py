"""UBOS 2024 census subcounty Excel: raw bounded rows and metadata."""
import release_runtime
import io, subprocess, openpyxl
from datetime import date, datetime, time

def _cell(value):
    return value.isoformat() if isinstance(value, (date, datetime, time)) else value
URL = 'https://statistics.ubos.org/nphc/resources/NPHC-2024-Subcounty-Profiles-Excel-Tables.xlsx'
PAGE = 'https://statistics.ubos.org/nphc/report?cat=resources'

def _book():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '65', '--max-filesize', '18000000', URL], capture_output=True, timeout=70)
    if p.returncode:
        raise RuntimeError('UBOS workbook download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 18000000 or not p.stdout.startswith(b'PK'):
        raise RuntimeError('Invalid or oversized workbook')
    return openpyxl.load_workbook(io.BytesIO(p.stdout), read_only=True, data_only=True)

def catalogue():
    w = _book()
    try:
        s = w['Table_of_Contents']
        items = []
        for row in s.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1]:
                items.append({'sheet': str(row[0]), 'title': str(row[1])})
        return {'source': 'Uganda Bureau of Statistics 2024 NPHC', 'url': URL, 'source_page': PAGE, 'items': items, 'note': '15 tables listed; only samples of Table1, Table2 and Table6 were inspected. Data are census statistics, not latest projections. Table headings and geographic hierarchy must be checked.'}
    finally:
        w.close()

def read(sheet, start=1, limit=15):
    if not isinstance(sheet, str) or sheet not in ['Table' + str(i) for i in range(1, 16)]:
        raise ValueError('sheet must be Table1–Table15')
    if isinstance(start, bool) or not isinstance(start, int) or start < 1 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('invalid row bounds')
    w = _book()
    try:
        s = w[sheet]
        if s.max_row > 100000 or s.max_column > 250:
            raise RuntimeError('Unexpected workbook dimensions')
        header = [{'row': n, 'cells': [_cell(v) for v in r]} for n, r in enumerate(s.iter_rows(min_row=1, max_row=6, values_only=True), 1)]
        rows = [{'row': n, 'cells': [_cell(v) for v in r]} for n, r in enumerate(s.iter_rows(min_row=start, max_row=min(start + limit - 1, s.max_row), values_only=True), start)] if start <= s.max_row else []
        return {'source': 'Uganda Bureau of Statistics 2024 NPHC', 'url': URL, 'sheet': sheet, 'total_rows': s.max_row, 'total_columns': s.max_column, 'headers': header, 'items': rows, 'note': 'Raw cached cells with original row coordinates. Geography names repeat at different administrative levels; inspect surrounding rows and original formatting. Headers may be merged or multi-row; no population aggregation or statistical transformation.'}
    finally:
        w.close()

def search(sheet, keyword, offset=0, limit=10):
    if not isinstance(sheet, str) or sheet not in ['Table' + str(i) for i in range(1, 16)] or (not isinstance(keyword, str)) or (not keyword.strip()) or (len(keyword) > 100):
        raise ValueError('invalid sheet or keyword')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 30):
        raise ValueError('invalid pagination')
    w = _book()
    try:
        s = w[sheet]
        if s.max_row > 100000 or s.max_column > 250:
            raise RuntimeError('Unexpected workbook dimensions')
        headers = [{'row': n, 'cells': [_cell(v) for v in r]} for n, r in enumerate(s.iter_rows(min_row=1, max_row=6, values_only=True), 1)]
        items = []
        count = 0
        for n, row in enumerate(s.iter_rows(min_row=7, values_only=True), 7):
            if row[0] is None or str(row[0]).strip().casefold() != keyword.strip().casefold():
                continue
            if offset <= count < offset + limit:
                items.append({'row': n, 'cells': [_cell(v) for v in row]})
            count += 1
        return {'source': 'Uganda Bureau of Statistics 2024 NPHC', 'url': URL, 'sheet': sheet, 'keyword': keyword, 'matches': count, 'offset': offset, 'headers': headers, 'items': items, 'note': 'Exact name search in first column; repeated names can represent different administrative levels or locations. Use read() to examine surrounding rows and original styling. Multiple nested totals overlap; do not sum blindly. Raw cells are cached values, not computed changes.'}
    finally:
        w.close()
