"""财政部农村危房改造补助资金分配原表。"""
import release_runtime
import hashlib, io, sys
from pathlib import Path
import requests
DATA = {2022: ('202205/t20220507_3808492.htm', '202205/W020220506583025057346.xlsx'), 2023: ('202307/t20230726_3898535.htm', '202307/W020230726556074823197.xls'), 2024: ('202404/t20240426_3933672.htm', '202404/P020240426640743386705.xls'), 2025: ('202504/t20250425_3962780.htm', '202504/P020250425705097582030.xls'), 2026: ('202608/t20260806_3995063.htm', '202608/P020260806615393824117.xlsx')}
BASE = 'https://sbs.mof.gov.cn/zxzyzf/ncwfgzbzzj/'

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持 2022–2026 年')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('无效筛选词')
    article, path = DATA[year]
    url = BASE + path
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000:
        raise ValueError('文件过大')
    if raw.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        try:
            import xlrd
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
            import xlrd
        book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
        sheets = [(s.name, [s.row_values(i) for i in range(s.nrows)], [list(x) for x in s.merged_cells]) for s in book.sheets() if s.nrows <= 10000 and s.ncols <= 256]
    elif raw.startswith(b'PK\x03\x04'):
        import openpyxl
        book = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
        sheets = []
        for s in book:
            if s.max_row > 10000 or s.max_column > 256:
                raise ValueError('表格尺寸异常')
            sheets.append((s.title, [[v if v is not None else '' for v in row] for row in s.iter_rows(values_only=True)], [str(x) for x in s.merged_cells.ranges]))
    else:
        raise ValueError('附件并非预期 Excel')
    result = []
    q = ''.join(keyword.split())
    for name, rows, merges in sheets:
        for row in rows:
            while row and row[-1] == '':
                row.pop()
        selected = [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if not q or q in ''.join((''.join(str(c).split()) for c in row))]
        result.append({'sheet': name, 'headers': rows[:6], 'rows': selected, 'merged_cells': merges})
    return {'source': '财政部住房城乡建设部中央财政农村危房改造补助资金分配表', 'year': year, 'article_url': BASE + article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': result, 'note': '原表为预算分配而非实际支出；单位、提前下达、本次下达和地区范围以每年原表为准，合计和组成不得重复加总。未列地区不等于零；本次下达出现负数为原表预算调整。XLS 合并范围为左闭右开坐标，XLSX 为单元格范围。'}
