"""财政部现代职业教育质量提升计划资金预算原表。"""
import release_runtime
import hashlib, io, sys
from pathlib import Path
import requests
DATA = {2021: ('https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202105/t20210519_3704966.htm', 'https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202105/P020210519576253610182.xlsx'), 2022: ('https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202204/t20220429_3807447.htm', 'https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202204/P020220429312416768568.xls'), 2023: ('https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202305/t20230504_3882236.htm', 'https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202305/P020230504615875513199.xls'), 2024: ('https://www.mof.gov.cn/jrttts/202405/t20240509_3934432.htm', 'https://www.mof.gov.cn/jrttts/202405/P020240509626600870987.xls'), 2025: ('https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202505/t20250519_3964085.htm', 'https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202505/P020250519638581572549.xls'), 2026: ('https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202606/t20260612_3991530.htm', 'https://jkw.mof.gov.cn/zxzyzf/xdzyjyzltsjhzxzj/202606/P020260612438779143169.xls')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持 2021–2026 年')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('无效筛选词')
    article, url = DATA[year]
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
    return {'source': '财政部现代职业教育质量提升计划资金预算表', 'year': year, 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': result, 'note': '原表为预算分配而非实际支出；单位和提前下达、本次下达等列以每年原表为准；地区是否含计划单列市须依原表标注，不重复加总。XLS 合并范围为左闭右开坐标，XLSX 为单元格范围。'}
