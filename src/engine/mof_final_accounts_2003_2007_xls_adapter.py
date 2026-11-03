"""MOF 2003–2007 national fiscal final account official XLS workbooks."""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
SOURCES = {2003: 'https://yss.mof.gov.cn/caizhengshuju/201007/P020190408362360894670.xls', 2004: 'https://yss.mof.gov.cn/caizhengshuju/201007/P020190408362645905132.xls', 2005: 'https://yss.mof.gov.cn/caizhengshuju/201007/P020190408362887511353.xls', 2006: 'https://yss.mof.gov.cn/caizhengshuju/201007/P020190408363477415830.xls', 2007: 'https://yss.mof.gov.cn/caizhengshuju/200809/P020080902561009672035.xls'}
INDEX = 'https://yss.mof.gov.cn/caizhengshuju/index_5.htm'

def catalog():
    return [{'year': y, 'url': u} for y, u in sorted(SOURCES.items())]

def _book(year):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2003–2007')
    with requests.get(SOURCES[year], timeout=(10, 40), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 10000000:
                raise ValueError('file too large')
    if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('invalid XLS')
    return (xlrd.open_workbook(file_contents=bytes(raw), formatting_info=True), hashlib.sha256(raw).hexdigest())

def sheets(year):
    book, digest = _book(year)
    return {'source': '财政部全国财政决算原始工作簿', 'year': year, 'index_url': INDEX, 'xls_url': SOURCES[year], 'sha256': digest, 'sheets': [{'index': i, 'name': s.name, 'rows': s.nrows, 'cols': s.ncols} for i, s in enumerate(book.sheets())]}

def rows(year, sheet_index, keyword='', offset=0, limit=100):
    if type(sheet_index) is not int or sheet_index < 0 or (not isinstance(keyword, str)) or (len(keyword) > 100) or (type(offset) is not int) or (offset < 0) or (type(limit) is not int) or (not 1 <= limit <= 500):
        raise ValueError('invalid sheet, keyword, offset or limit')
    book, digest = _book(year)
    if sheet_index >= book.nsheets:
        raise ValueError('sheet index out of range')
    s = book.sheet_by_index(sheet_index)
    if s.nrows > 5000 or s.ncols > 100:
        raise ValueError('unexpected table size')

    def row(n):
        return {'row': n + 1, 'cells': [{'value': s.cell_value(n, c), 'cell_type': s.cell_type(n, c)} for c in range(s.ncols)]}
    matches = [n for n in range(s.nrows) if keyword in ' '.join((str(s.cell_value(n, c)) for c in range(s.ncols)))]
    return {'source': '财政部全国财政决算原始工作簿', 'year': year, 'xls_url': SOURCES[year], 'sha256': digest, 'sheet_name': s.name, 'total_rows': s.nrows, 'matched_rows': len(matches), 'offset': offset, 'headers': [row(n) for n in range(min(5, s.nrows))], 'rows': [row(n) for n in matches[offset:offset + limit]], 'truncated': len(matches) > offset + limit, 'merged_ranges': [{'start_row': a + 1, 'end_row': b, 'start_col': c + 1, 'end_col': d} for a, b, c, d in s.merged_cells], 'note': '原始数字可能有隐藏小数；各列含预算/决算/比例等，单位及范围须核原表；空白非零。'}
