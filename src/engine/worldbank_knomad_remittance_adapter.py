"""KNOMAD annual remittance inflows and outflows, September 2025 workbook."""
import release_runtime
import io, subprocess
import openpyxl
BASE = 'https://datacatalogfiles.worldbank.org/ddh-published/0066146/'
FILES = {'inward': ('DR0095569/Inward_remittance_flows_%28September_2025%29.xlsx', 'Inward remittance flows'), 'outward': ('DR0095570/Outward_remittance_flows_%28September_2025%29.xlsx', 'Outward remittance flows')}
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0066146/knomad'

def query(keyword, direction, start, end):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('invalid jurisdiction keyword')
    if direction not in FILES:
        raise ValueError('invalid direction')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 2000 <= x <= 2024) for x in (start, end))) or start > end:
        raise ValueError('years must be in 2000–2024')
    path, sheetname = FILES[direction]
    url = BASE + path
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', '2000000', url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 2000000:
        raise ValueError('file exceeds 2 MB')
    wb = openpyxl.load_workbook(io.BytesIO(r.stdout), read_only=True, data_only=True)
    try:
        rows = wb[sheetname].iter_rows(values_only=True)
        h = next(rows)
        if not str(h[0]).startswith('Remittance '):
            raise ValueError('unexpected workbook format')
        records = []
        for row in rows:
            if isinstance(row[0], str) and keyword.casefold() in row[0].casefold():
                observations = [{'column': i + 1, 'year': int(str(v)), 'value': row[i]} for i, v in enumerate(h) if str(v).isdigit() and start <= int(str(v)) <= end]
                extras = [{'column': i + 1, 'header': v, 'value': row[i]} for i, v in enumerate(h) if i > 0 and v is not None and (not str(v).isdigit())]
                records.append({'jurisdiction': row[0], 'observations': observations, 'other_fields': extras})
        return {'source': url, 'catalog': CATALOG, 'version': 'September 2025', 'unit': h[0], 'records': records, 'note': 'Inward and outward flows are distinct; original zeros and empty cells are retained. This historical 2000–2024 workbook includes national and aggregate rows: geographic aggregates overlap countries and should not be added to them. A returned zero is the source value and does not by itself establish complete reporting. Country names are source labels matched case-insensitively; verify the chosen jurisdiction.'}
    finally:
        wb.close()
