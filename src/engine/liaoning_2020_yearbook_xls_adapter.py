"""Official Liaoning 2020 yearbook ZIP: individual XLS tables."""
import release_runtime
import io
import re
import sys
import zipfile
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
INDEX = 'https://tjj.ln.gov.cn/tjj/tjsj/tjnj/njsjxz/2023110210085021756/index.shtml'
URL = 'https://tjj.ln.gov.cn/tjj/tjsj/tjnj/njsjxz/2023110210085021756/2025010614482229551.zip'

def _zip():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK\x03\x04'):
        raise ValueError('response is not ZIP')
    return zipfile.ZipFile(io.BytesIO(r.content))

def catalog():
    z = _zip()
    out = []
    for info in z.infolist():
        name = info.filename.rsplit('/', 1)[-1]
        if re.fullmatch('\\d{2}-\\d{2}[A-Za-z0-9_-]*\\.xls', name, re.I):
            out.append({'id': name[:-4], 'filename': name, 'bytes': info.file_size})
    if not out:
        raise ValueError('no yearbook XLS files found')
    return {'source': '辽宁省统计局《辽宁统计年鉴2020》', 'edition': 2020, 'source_url': URL, 'index_url': INDEX, 'items': out}

def table(table_id):
    if not isinstance(table_id, str) or not re.fullmatch('\\d{2}-\\d{2}[A-Za-z0-9_-]*', table_id):
        raise ValueError('invalid table ID')
    z = _zip()
    matches = [x for x in z.infolist() if x.filename.rsplit('/', 1)[-1].lower() == (table_id + '.xls').lower()]
    if len(matches) != 1:
        raise ValueError('table ID missing or ambiguous')
    book = xlrd.open_workbook(file_contents=z.read(matches[0]), formatting_info=True)
    sheets = []
    for s in book.sheets():
        sheets.append({'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(m) for m in s.merged_cells]})
    return {'source': '辽宁省统计局《辽宁统计年鉴2020》', 'edition': 2020, 'id': table_id, 'source_url': URL, 'index_url': INDEX, 'sheets': sheets, 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
