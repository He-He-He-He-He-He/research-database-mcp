"""财政部基本公共卫生服务补助资金分配原表。"""
import release_runtime
import hashlib, io, sys
from pathlib import Path
import requests
DATA = {2021: ('202011/t20201124_3628791.htm', '202011/P020201124545149161118.xlsx'), 2024: ('202405/t20240514_3934779.htm', '202405/P020240514582129827567.xls')}
BASE = 'https://sbs.mof.gov.cn/zxzyzf/ggwsfwbzzj/'

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持 2021 和 2024 年')
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
    return {'source': '财政部国家卫生健康委基本公共卫生服务补助资金分配表', 'year': year, 'article_url': BASE + article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': result, 'note': '2021仅提前下达，2024为年度应补助预算，不能直接比较；2024地区下列有其中子项，禁止重复相加。预算非实际支出。单位按原表，常住人口列是万人、资金是万元。XLS 合并范围为左闭右开坐标，XLSX 为单元格范围。'}
