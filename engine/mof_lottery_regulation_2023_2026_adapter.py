"""财政部彩票市场调控资金预算原表。"""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
DATA = {2023: ('https://zhs.mof.gov.cn/zhengcefabu/202305/t20230505_3882538.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202305/P020230505576363368442.xls', '年度预算'), 2024: ('https://zhs.mof.gov.cn/zhengcefabu/202405/t20240524_3935638.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202405/P020240524561263877371.xls', '年度预算'), 2025: ('https://zhs.mof.gov.cn/zhengcefabu/202505/t20250522_3964364.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202505/P020250522644122864041.xls', '年度预算'), 2026: ('https://zhs.mof.gov.cn/zhengcefabu/202605/t20260509_3989356.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202605/P020260509600334945577.xls', '年度预算')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持2023–2026')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('筛选词无效')
    article, url, stage = DATA[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000 or not raw.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('附件并非预期XLS')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    out = []
    q = ''.join(keyword.split())
    for s in book.sheets():
        if s.nrows > 10000 or s.ncols > 256:
            raise ValueError('表尺寸异常')
        rows = [s.row_values(i) for i in range(s.nrows)]
        for row in rows:
            while row and row[-1] == '':
                row.pop()
        out.append({'sheet': s.name, 'headers': rows[:6], 'rows': [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if not q or q in ''.join((''.join(str(c).split()) for c in row))], 'merged_cells': [list(x) for x in s.merged_cells]})
    return {'source': '财政部彩票市场调控资金预算分配表', 'year': year, 'stage': stage, 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': out, 'note': '这是彩票市场调控资金预算，不是彩票销售额或公益金，也非实际支出；单位及地区范围以原表为准，预算数、提前下达及此次下达不得重复相加。合并区域为左闭右开坐标。'}
