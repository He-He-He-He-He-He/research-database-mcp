"""WTO Global Trade Outlook and Statistics April 2025 workbook."""
import release_runtime
import argparse, datetime, hashlib, io, json
import requests, openpyxl
URL = 'https://www.wto.org/english/res_e/booksp_e/trade_outlook25_data_e.xlsx'
PAGE = 'https://www.wto.org/english/res_e/publications_e/trade_outlook25_e.htm'

def query(sheet='Contents', start=1, end=100):
    if not isinstance(sheet, str) or not sheet or len(sheet) > 100 or any((type(x) is not int for x in (start, end))) or (not 1 <= start <= end <= 500) or (end - start > 199):
        raise ValueError('invalid sheet or range')
    with requests.get(URL, stream=True, timeout=30) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(5000001, decode_content=True)
    if len(raw) > 5000000:
        raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=False, data_only=True)
    try:
        if sheet not in w.sheetnames:
            raise ValueError('unknown sheet; query Contents for sheet catalog')
        s = w[sheet]
        rows = []
        for row in s.iter_rows(min_row=start, max_row=min(end, s.max_row)):
            cells = []
            for c in row:
                if c.value is None:
                    continue
                v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
                cells.append({'cell': c.coordinate, 'value': v, 'number_format': c.number_format})
            if cells:
                rows.append({'row': row[0].row, 'cells': cells})
        return {'source': URL, 'report_page': PAGE, 'edition': 'April 2025', 'http_last_modified': modified, 'workbook_created': str(w.properties.created), 'workbook_modified': str(w.properties.modified), 'source_sha256': hashlib.sha256(raw).hexdigest(), 'available_sheets': w.sheetnames, 'sheet': sheet, 'row_range': [start, end], 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'rows': rows, 'note': 'WTO Secretariat historical report: retain all titles, multi-row headings, footnotes, original numbers and units. 2025–2026 columns may be projections; baseline and adjusted scenarios are distinct. Values are cached workbook results, not recalculated formulas. Blank cells, including merged cells, are not zeros. Current file metadata and HTTP dates do not independently prove immutable archive identity; consult WTO usage terms.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sheet', default='Contents')
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--end', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.sheet, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
