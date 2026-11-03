"""ANSADE 2023 census wilaya indicators workbook; preserve raw cells and header merges."""
import release_runtime
import io, subprocess, datetime, openpyxl
PAGE = 'https://admin.ansade.mr/indicateurs-demographiques-et-socioeconomiques-pour-les-wilayas/'
URL = 'https://admin.ansade.mr/wp-content/uploads/2024/08/Indicateurs-demographiques-et-socioeconomiques_Wilaya1408-1.xlsx'

def _book():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '40', '--max-filesize', '5000000', URL], capture_output=True, timeout=45)
    if p.returncode:
        raise RuntimeError('ANSADE workbook download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 5000000 or not p.stdout.startswith(b'PK'):
        raise RuntimeError('Invalid workbook')
    return openpyxl.load_workbook(io.BytesIO(p.stdout), read_only=False, data_only=True)

def _val(v):
    return v.isoformat() if isinstance(v, (datetime.datetime, datetime.date, datetime.time)) else v

def catalogue():
    w = _book()
    try:
        return {'source': 'ANSADE Mauritania RGPH 2023', 'source_page': PAGE, 'workbook_url': URL, 'items': [{'sheet': s.title, 'rows': s.max_row, 'columns': s.max_column} for s in w], 'note': 'Source workbook has six sheets for total/urban/rural population and households. Counts may be noninteger and some headings do not clearly match the magnitude of values; do not round or infer units without official methodology.'}
    finally:
        w.close()

def table(sheet, start=1, limit=10, max_cols=12):
    if not isinstance(sheet, str) or len(sheet) > 60:
        raise ValueError('invalid sheet')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, limit, max_cols))) or start < 1 or (not 1 <= limit <= 50) or (not 1 <= max_cols <= 190):
        raise ValueError('invalid bounds')
    w = _book()
    try:
        if sheet not in w.sheetnames:
            raise ValueError('Unknown sheet; use catalogue for exact names including trailing spaces')
        s = w[sheet]
        if s.max_row > 1000 or s.max_column > 250:
            raise RuntimeError('Unexpected workbook dimensions')

        def row(n):
            return {'row': n, 'cells': [_val(c.value) for c in s[n][:max_cols]]}
        merges = [str(r) for r in s.merged_cells.ranges if r.min_row <= 5 and r.min_col <= max_cols]
        return {'source': 'ANSADE Mauritania RGPH 2023', 'source_page': PAGE, 'workbook_url': URL, 'sheet': sheet, 'total_rows': s.max_row, 'total_columns': s.max_column, 'header_rows': [row(n) for n in range(1, min(s.max_row, 5) + 1)], 'header_merged_ranges': merges, 'items': [row(n) for n in range(start, min(start + limit, s.max_row + 1))], 'note': 'Raw cached cells and original coordinates. Counts contain fractional values; e.g. population total 4,927,532.3126759315. Headings include five-year age (%) while values may resemble counts. Unit, statistical weighting, and denominators require official verification. Headers and footnotes may be outside selected columns; total/urban/rural overlap.'}
    finally:
        w.close()
