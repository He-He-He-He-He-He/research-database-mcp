"""Read official Yunnan 2023 economic census Excel ZIP without extracting files."""
import release_runtime
import io, sys, zipfile
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
URL = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/202512/P020260622405760973906.zip'
PAGE = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/202512/t20251230_3052695.html'

def _archive():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if len(r.content) > 30000000:
        raise ValueError('Unexpected archive size')
    return zipfile.ZipFile(io.BytesIO(r.content))

def catalog(keyword=''):
    with _archive() as z:
        items = [{'id': i.filename, 'size': i.file_size} for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith('.xls') and (keyword.lower() in i.filename.lower())]
    return {'source': '云南省统计局', 'book': '云南经济普查年鉴2023', 'source_page': PAGE, 'archive_url': URL, 'items': items}

def table(table_id):
    if not isinstance(table_id, str):
        raise ValueError('table ID must be a string from catalog')
    with _archive() as z:
        matches = [i for i in z.infolist() if i.filename == table_id and i.filename.lower().endswith('.xls') and (not i.is_dir())]
        if len(matches) != 1:
            raise ValueError('unknown or ambiguous table ID')
        if matches[0].file_size > 30000000:
            raise ValueError('unusually large table')
        data = z.read(matches[0])
    if not data.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('not an XLS workbook')
    w = xlrd.open_workbook(file_contents=data, formatting_info=True)
    return {'source': '云南省统计局', 'book': '云南经济普查年鉴2023', 'source_page': PAGE, 'archive_url': URL, 'id': table_id, 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in w.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
