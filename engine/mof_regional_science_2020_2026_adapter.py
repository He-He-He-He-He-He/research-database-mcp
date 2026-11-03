"""财政部中央引导地方科技发展资金预算原表。"""
import release_runtime
import hashlib, io, sys
from pathlib import Path
import requests
DATA = {2020: ('https://jkw.mof.gov.cn/zxzyzf/zyczyddfkjfzzj/202007/t20200703_3543284.htm', 'https://jkw.mof.gov.cn/zxzyzf/zyczyddfkjfzzj/202007/P020200703514041343429.xlsx'), 2021: ('https://www.mof.gov.cn/gp/xxgkml/kjs/202105/t20210512_3701046.htm', 'https://www.mof.gov.cn/gp/xxgkml/kjs/202105/P020210512635507541062.xls'), 2022: ('https://jkw.mof.gov.cn/zxzyzf/zyczyddfkjfzzj/202204/t20220429_3807721.htm', 'https://jkw.mof.gov.cn/zxzyzf/zyczyddfkjfzzj/202204/P020220429632256753741.xls'), 2023: ('https://jkw.mof.gov.cn/zxzyzf/zyczyddfkjfzzj/202211/t20221121_3852546.htm', 'https://jkw.mof.gov.cn/zxzyzf/zyczyddfkjfzzj/202211/P020221121614332495612.xls'), 2024: ('https://jkw.mof.gov.cn/gongzuotongzhi/202404/t20240430_3933935.htm', 'https://jkw.mof.gov.cn/gongzuotongzhi/202404/P020240430615146265983.xlsx'), 2025: ('https://jkw.mof.gov.cn/gongzuotongzhi/202505/t20250508_3963426.htm', 'https://jkw.mof.gov.cn/gongzuotongzhi/202505/P020250508738633451444.xls'), 2026: ('https://jkw.mof.gov.cn/gongzuotongzhi/202605/t20260508_3989230.htm', 'https://jkw.mof.gov.cn/gongzuotongzhi/202605/P020260508302605240522.xls')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持 2020–2026 年')
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
    return {'source': '财政部中央引导地方科技发展资金预算分配总表', 'year': year, 'stage': '提前下达部分' if year == 2023 else '年度预算', 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': result, 'note': '2023年只有提前下达部分，不能与其他年年度预算总量直接比较。原表为预算分配而非实际支出；单位和提前下达、本次下达等列以每年原表为准；地区是否含计划单列市须依原表标注，不重复加总。XLS 合并范围为左闭右开坐标，XLSX 为单元格范围。'}
