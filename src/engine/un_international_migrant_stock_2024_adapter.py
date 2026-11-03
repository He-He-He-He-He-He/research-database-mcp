"""UN Population Division International Migrant Stock 2024 by origin/destination and sex."""
import release_runtime
import io, re
import openpyxl, requests
ROOT = 'https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/'
FILES = {'destination': 'undesa_pd_2024_ims_stock_by_sex_and_destination.xlsx', 'origin': 'undesa_pd_2024_ims_stock_by_sex_and_origin.xlsx'}
YEARS = (1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024)
PAGE = 'https://www.un.org/development/desa/pd/content/international-migrant-stock/'
NOTE = 'UN DESA Population Division International Migrant Stock 2024: estimates at mid-year, not annual inflows, citizenship acquisitions, employment or persons with permission to work. Origin means birthplace/citizenship of those living outside it; destination means residence. Birthplace is preferred; citizenship is used where birthplace unavailable. Source type B/C/R/I and coverage markers are kept verbatim. R adds certain refugee/asylum/displacement populations. Unlisted/empty is not zero. Regional/global aggregates overlap countries and sex totals overlap subgroups; never add them together. 2024 edition re-assessed 60 economies, others extrapolate 2020 edition; historical values are estimates and may be revised. CC BY 3.0 IGO. Consult workbook notes for coverage and definitions.'

def query(direction, code, start=1990, end=2024, session=None):
    if direction not in FILES:
        raise ValueError('direction must be origin or destination')
    if type(code) is not int or not 0 <= code <= 9999:
        raise ValueError('code must be M49 integer')
    if any((type(v) is not int for v in (start, end))) or start > end or start < 1990 or (end > 2024):
        raise ValueError('invalid year range')
    url = ROOT + FILES[direction]
    h = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'Referer': PAGE}
    r = (session or requests).get(url, headers=h, timeout=45)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('workbook too large')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        if 'Table 1' not in w.sheetnames or 'Migrant notes' not in w.sheetnames:
            raise ValueError('unexpected workbook')
        sh = w['Table 1']
        title = sh.cell(3, 6).value
        header = [sh.cell(11, i).value for i in range(6, 30)]
        if not isinstance(title, str) or direction not in title.lower() or tuple(header) != YEARS * 3:
            raise ValueError('unexpected table header')
        found = []
        for row in sh.iter_rows(min_row=12, values_only=True):
            if len(row) > 4 and row[4] == code:
                found.append(row)
        if len(found) > 1:
            raise ValueError('duplicate location code')
        if not found:
            return {'direction': direction, 'code': code, 'items': [], 'source': url, 'note': NOTE}
        row = found[0]
        items = []
        for i, year in enumerate(YEARS):
            if start <= year <= end:
                items.append({'year': year, 'both_sexes': row[5 + i], 'male': row[13 + i], 'female': row[21 + i]})
        return {'direction': direction, 'code': code, 'location': row[1], 'coverage_note_marker': row[2], 'data_type_raw': row[3], 'table_title': title, 'unit': 'persons', 'items': items, 'source': url, 'note': NOTE}
    finally:
        w.close()
