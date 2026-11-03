"""UN Demographic Yearbook 2023 official XLS tables."""
import release_runtime
import argparse, hashlib, json, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://unstats.un.org/unsd/demographic-social/products/dyb/documents/dyb2023/'
PAGE = 'https://unstats.un.org/unsd/demographic-social/products/dyb/dyb_2023/'
TABLES = {f'{n:02}' for n in range(1, 26)} | {'03a'}

def query(table, sheet='Data', keyword='', start=1, end=100, limit=20):
    if table not in TABLES or sheet not in ('Data', 'Footnotes') or (not isinstance(keyword, str)) or (len(keyword) > 100):
        raise ValueError('invalid table, sheet or keyword')
    if any((type(v) is not int for v in (start, end, limit))) or not 1 <= start <= end <= 100000 or end - start > 9999 or (not 1 <= limit <= 100):
        raise ValueError('invalid row range or limit')
    url = BASE + 'table' + table + '.xls'
    with requests.get(url, stream=True, timeout=45) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(8000001, decode_content=True)
    if len(raw) > 8000000:
        raise ValueError('workbook too large')
    w = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    if sheet not in w.sheet_names():
        raise ValueError('sheet unavailable; inspect original workbook')
    s = w.sheet_by_name(sheet)

    def serial(i):
        cells = []
        for j, c in enumerate(s.row(i)):
            if c.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                continue
            v = xlrd.error_text_from_code.get(c.value, str(c.value)) if c.ctype == xlrd.XL_CELL_ERROR else c.value
            cells.append({'column': j + 1, 'value': v, 'cell_type': c.ctype})
        return {'row': i + 1, 'cells': cells}
    hits = []
    matches = 0
    for i in range(start - 1, min(end, s.nrows)):
        if keyword and (not any((keyword.casefold() in str(c.value).casefold() for c in s.row(i)))):
            continue
        if not any((c.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK) for c in s.row(i))):
            continue
        matches += 1
        if len(hits) < limit:
            item = serial(i)
            if keyword and i + 1 < s.nrows:
                item['next_row'] = serial(i + 1)
            hits.append(item)
    return {'source': url, 'report_page': PAGE, 'edition': '2023', 'sheet': sheet, 'available_sheets': w.sheet_names(), 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'sheet_rows': s.nrows, 'sheet_columns': s.ncols, 'range': [start, end], 'matched_count': matches, 'merged_ranges_zero_based_exclusive': [list(v) for v in s.merged_cells], 'rows': hits, 'note': 'UN Demographic Yearbook 2023: source data are official national submissions where available, and definitions, units and years vary by table and country. Country labels and values may occupy consecutive rows; inspect headings and Footnotes sheet. Blank and symbol values are not automatically interpreted. Last-Modified and checksum do not independently establish historical archive immutability. All 26 official XLS files were downloaded and opened during verification; Data and Footnotes sheet presence was checked, but individual values and footnotes were not exhaustively validated.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('table', choices=sorted(TABLES))
    p.add_argument('--sheet', choices=['Data', 'Footnotes'], default='Data')
    p.add_argument('--keyword', default='')
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--end', type=int, default=100)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.table, a.sheet, a.keyword, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
