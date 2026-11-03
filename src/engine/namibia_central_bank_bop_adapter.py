"""Bank of Namibia official Balance of Payment Aggregates XLSX, read-only."""
import release_runtime
import io, re, subprocess
from datetime import date, datetime, time
from openpyxl import load_workbook
INFO = 'https://www.bon.com.na/Economic-information/Statistical-information/Open-Data-Platform-%28ODP%29.aspx'
URL = 'https://www.bon.com.na/getattachment/18f77239-0d27-426b-b531-11e0b7b31906/.aspx'
MAX = 15000000

def _book():
    p = release_runtime.run(['/usr/bin/curl', '-fLsS', '--max-time', '45', '--max-filesize', str(MAX), URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('Bank of Namibia download failed: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > MAX or p.stdout[:2] != b'PK':
        raise RuntimeError('Unexpected or oversized workbook')
    return load_workbook(io.BytesIO(p.stdout), read_only=True, data_only=True)

def _cell(v):
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)

def catalogue():
    w = _book()
    try:
        return {'source': 'Bank of Namibia', 'source_page': INFO, 'workbook_url': URL, 'items': [{'sheet': s.title, 'max_row': s.max_row, 'max_column': s.max_column} for s in w.worksheets], 'note': '工作表尺寸可能包含空白单元；以原表标题、表头和注释为准。实时下载工作簿，不承诺所有表均已验证。'}
    finally:
        w.close()

def search(sheet, keyword, offset=0, limit=10):
    if not isinstance(sheet, str) or not sheet.strip() or len(sheet) > 60:
        raise ValueError('Invalid sheet')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('Invalid keyword')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 30):
        raise ValueError('Invalid pagination')
    w = _book()
    try:
        if sheet not in w.sheetnames:
            raise ValueError('Sheet absent in official workbook')
        s = w[sheet]
        if s.max_row > 10000 or s.max_column > 250:
            raise RuntimeError('Workbook sheet exceeds bounded reader limits')
        headers = []
        matches = []
        n = 0
        for idx, row in enumerate(s.iter_rows(values_only=True), start=1):
            vals = [_cell(x) for x in row]
            if idx <= 4:
                headers.append({'row': idx, 'cells': vals})
            if keyword.casefold() in ' '.join((str(v) for v in vals if isinstance(v, str))).casefold():
                if offset <= n < offset + limit:
                    matches.append({'row': idx, 'cells': vals})
                n += 1
        return {'source': 'Bank of Namibia', 'source_page': INFO, 'workbook_url': URL, 'sheet': sheet, 'query': keyword, 'header_rows': headers, 'matches': n, 'offset': offset, 'items': matches, 'note': '原始行与前4行表头按原坐标返回；各表表头结构可能不同，需结合全部原工作簿、脚注、公式缓存、时间、单位和初步状态核验；未经排序或同比换算，非实时汇率。'}
    finally:
        w.close()
