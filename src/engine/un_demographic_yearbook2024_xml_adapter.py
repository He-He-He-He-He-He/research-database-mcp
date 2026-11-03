"""UN Demographic Yearbook 2024 SpreadsheetML tables (.xls XML)."""
import release_runtime
import argparse, hashlib, json, xml.etree.ElementTree as ET
import requests
BASE = 'https://unstats.un.org/unsd/demographic-social/products/dyb/documents/DYB2024/'
PAGE = 'https://unstats.un.org/unsd/demographic-social/products/dyb/dyb_2024/'
NS = 'urn:schemas-microsoft-com:office:spreadsheet'
N = '{' + NS + '}'
TABLES = {f'{n:02}' for n in range(1, 26)} | {'03a'}

def query(table, sheet='Data', keyword='', start=1, end=100, limit=20):
    if table not in TABLES or sheet not in ('Data', 'Footnotes') or (not isinstance(keyword, str)) or (len(keyword) > 100):
        raise ValueError('invalid query')
    if any((type(x) is not int for x in (start, end, limit))) or not 1 <= start <= end <= 100000 or end - start > 9999 or (not 1 <= limit <= 100):
        raise ValueError('invalid range')
    url = BASE + 'table' + table + '.xls'
    with requests.get(url, stream=True, timeout=45) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(20000001, decode_content=True)
    if len(raw) > 20000000:
        raise ValueError('workbook too large')
    root = ET.fromstring(raw)
    if root.tag != N + 'Workbook':
        raise ValueError('unexpected SpreadsheetML root')
    sheets = {w.get(N + 'Name'): w for w in root.findall(N + 'Worksheet')}
    if sheet not in sheets:
        raise ValueError('sheet unavailable')
    table_node = sheets[sheet].find(N + 'Table')
    if table_node is None:
        raise ValueError('table element missing')
    rows = []
    num = 0
    for row in table_node.findall(N + 'Row'):
        num = int(row.get(N + 'Index', num + 1))
        col = 0
        cells = []
        for c in row.findall(N + 'Cell'):
            col = int(c.get(N + 'Index', col + 1))
            d = c.find(N + 'Data')
            value = ''.join(d.itertext()) if d is not None else None
            across = int(c.get(N + 'MergeAcross', '0'))
            down = int(c.get(N + 'MergeDown', '0'))
            if value is not None or across or down:
                cells.append({'column': col, 'value': value, 'source_type': d.get(N + 'Type') if d is not None else None, 'merge_across': across, 'merge_down': down})
            col += across
        rows.append({'row': num, 'cells': cells})
    selected = []
    total = 0
    for i, row in enumerate(rows):
        if not start <= row['row'] <= end or not row['cells']:
            continue
        if keyword and (not any((keyword.casefold() in str(c['value']).casefold() for c in row['cells']))):
            continue
        total += 1
        if len(selected) < limit:
            item = dict(row)
            if keyword and i + 1 < len(rows):
                item['next_row'] = rows[i + 1]
            selected.append(item)
    return {'source': url, 'report_page': PAGE, 'edition': '2024', 'sheet': sheet, 'available_sheets': list(sheets), 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'file_format': 'SpreadsheetML XML', 'matched_count': total, 'rows': selected, 'note': '2024 edition, not a proven pre-July-2025 source. XLS extension contains SpreadsheetML XML; source values and types retained as strings, including dates and missing symbols. Country data can occupy the next row. Consult original headings and Footnotes; estimates, definitions, units and years vary by country. Dates/checksum do not prove initial publication or historical immutability. Official index lists 26 files; 24 were downloaded and opened with Data and Footnotes verified, while tables 07 and 03a are large and full downloads remain unverified.'}

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
