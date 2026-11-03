"""US Census Bureau official 2022 NAICS structure and change indicators."""
import release_runtime
import hashlib
import io
import requests
import openpyxl
URL = 'https://www.census.gov/naics/2022NAICS/2022_NAICS_Structure.xlsx'
PAGE = 'https://www.census.gov/naics/'
NOTES = ['NAICS is an industry classification, not a firm register, GDP or employment count. Hierarchical rows overlap and must not be added as independent industries.', 'Use the full official NAICS manual for definitions and 2017-to-2022 concordances. The trailing T mark in source titles indicates trilateral agreement; raw titles are preserved.', 'Change indicators and their source legend are preserved. The file currently served may have been updated after the 2022 classification year and is not automatically a historical file snapshot.']

def search(keyword, limit=20, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid NAICS query')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('Census source is not XLSX')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    if '2022 NAICS Structure' not in w.sheetnames:
        raise ValueError('Unexpected NAICS workbook')
    s = w['2022 NAICS Structure']
    rows = s.iter_rows(values_only=True)
    title = next(rows)
    legend = next(rows)
    header = next(rows)
    if tuple(header[:3]) != ('Change Indicator', '2022 NAICS Code', '2022 NAICS Title'):
        raise ValueError('Unexpected NAICS headings')
    out = []
    k = keyword.casefold()
    for row in rows:
        marker, code, name = row[:3]
        if code is None and name is None:
            continue
        if code is None or not isinstance(name, str):
            raise ValueError('Unexpected NAICS row')
        if k in (str(code) + ' ' + name).casefold():
            out.append({'change_indicator_raw': marker, 'code_raw': str(code), 'title_raw': name})
    return {'source': URL, 'page': PAGE, 'edition': '2022', 'http_last_modified': r.headers.get('Last-Modified'), 'sha256': hashlib.sha256(r.content).hexdigest(), 'source_title': title[0], 'source_legend': legend[0], 'total_matching': len(out), 'offset': offset, 'notes': NOTES, 'records': out[offset:offset + limit]}
