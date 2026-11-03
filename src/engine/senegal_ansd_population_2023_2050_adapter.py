"""Senegal ANSD 2023 census baseline and subnational population projections."""
import release_runtime
import io, subprocess, openpyxl
URL = 'https://www.ansd.sn/sites/default/files/2024-11/Projections-demographiques_2023-2050.xlsx'
PAGE = 'https://www.ansd.sn/Indicateur/donnees-de-population'

def search(keyword, year, offset=0, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword required')
    if isinstance(year, bool) or not isinstance(year, int) or year not in range(2023, 2051):
        raise ValueError('year must be 2023–2050')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 50):
        raise ValueError('invalid pagination')
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '35', '--max-filesize', '5000000', URL], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('ANSD workbook request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 5000000 or not p.stdout.startswith(b'PK'):
        raise RuntimeError('Invalid ANSD workbook')
    w = openpyxl.load_workbook(io.BytesIO(p.stdout), read_only=True, data_only=True)
    try:
        if w.sheetnames != ['Projections démo 2023-2050']:
            raise RuntimeError('Unexpected sheets')
        s = w.active
        if s.max_row > 1000 or s.max_column > 200:
            raise RuntimeError('Unexpected workbook dimensions')
        col = 2 + (year - 2023) * 3
        date = s.cell(1, col).value
        if year == 2023 and date != 'RGPH-5 2023' or (year != 2023 and date != year):
            raise RuntimeError('Year header mismatch')
        headers = [s.cell(2, c).value for c in range(col, col + 3)]
        if headers != ['HOMME', 'FEMME', 'ENSEMBLE']:
            raise RuntimeError('Sex headers changed')
        results = []
        for n, row in enumerate(s.iter_rows(min_row=3, values_only=True), 3):
            name = row[0]
            if isinstance(name, str) and keyword.casefold() in name.casefold():
                results.append({'row': n, 'geography_raw': name, 'values_raw': {headers[i]: row[col - 1 + i] for i in range(3)}})
        return {'source': 'ANSD Sénégal', 'source_page': PAGE, 'workbook_url': URL, 'sheet': s.title, 'year': year, 'source_year_header': date, 'unit': 'persons', 'matches': len(results), 'offset': offset, 'items': results[offset:offset + limit], 'note': '2023 is the census baseline column; 2024–2050 are projections, not realized counts. Regions and their departments overlap and must not be summed together. The 2025 sum of 14 region totals is 19,075,962 while the ANSD indicator page states 19,075,959; source discrepancy is not resolved, do not silently reconcile.'}
    finally:
        w.close()
