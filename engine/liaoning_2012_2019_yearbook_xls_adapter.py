"""Official Liaoning statistical yearbooks, selected 2012–2019 XLS editions."""
import release_runtime
import io, re, sys, zipfile
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://tjj.ln.gov.cn/tjj/tjsj/tjnj/njsjxz/'
FILES = {2012: '2023110210084496668/2026073115372250505.zip', 2014: '2023110210084496668/2024042816043130655.zip', 2015: '2023110210084496668/2026073115395894171.zip', 2016: '2023110210084496668/2026073115573083538.zip', 2017: '2023110210084496668/2026073115570350228.zip', 2018: '2023110210084851581/2024042816144622966.zip', 2019: '2023110210084851581/2024042816145835780.zip'}

def _zip(year):
    if isinstance(year, bool) or not isinstance(year, int) or year not in FILES:
        raise ValueError('available editions: 2012, 2014–2019')
    url = BASE + FILES[year]
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK\x03\x04'):
        raise ValueError('not a ZIP file')
    return (zipfile.ZipFile(io.BytesIO(r.content)), url)

def catalog(year):
    z, url = _zip(year)
    items = []
    for x in z.infolist():
        n = x.filename.rsplit('/', 1)[-1]
        if re.fullmatch('[A-Za-z0-9_-]+\\.xls', n, re.I):
            items.append({'id': n[:-4], 'filename': n, 'bytes': x.file_size})
    if not items:
        raise ValueError('no XLS files found')
    return {'source': f'辽宁省统计局《辽宁统计年鉴{year}》', 'edition': year, 'source_url': url, 'items': items}

def table(year, table_id):
    if not isinstance(table_id, str) or not re.fullmatch('[A-Za-z0-9_-]+', table_id):
        raise ValueError('invalid table ID')
    z, url = _zip(year)
    matches = [x for x in z.infolist() if x.filename.rsplit('/', 1)[-1].lower() == (table_id + '.xls').lower()]
    if len(matches) != 1:
        raise ValueError('table ID missing or ambiguous')
    book = xlrd.open_workbook(file_contents=z.read(matches[0]), formatting_info=True)
    return {'source': f'辽宁省统计局《辽宁统计年鉴{year}》', 'edition': year, 'source_url': url, 'id': table_id, 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(m) for m in s.merged_cells]} for s in book.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
