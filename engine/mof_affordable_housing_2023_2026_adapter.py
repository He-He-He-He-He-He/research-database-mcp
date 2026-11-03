"""财政部城镇保障性安居工程补助资金预算原表。"""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
DATA = {2023: ('https://zhs.mof.gov.cn/zhengcefabu/202403/t20240325_3931376.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202403/P020240325646612995833.xls', '年度分配，分项目'), 2024: ('https://zhs.mof.gov.cn/zhengcefabu/202404/t20240416_3932833.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202404/P020240416331811325840.xls', '年度分配'), 2025: ('https://zhs.mof.gov.cn/zhengcefabu/202411/t20241108_3947199.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202411/P020241108599026011425.xls', '提前下达的部分预算'), 2026: ('https://zhs.mof.gov.cn/zhengcefabu/202511/t20251119_3976673.htm', 'https://zhs.mof.gov.cn/zhengcefabu/202511/P020251119354364189641.xls', '提前下达的部分预算')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持2023至2026')
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
    return {'source': '财政部中央财政城镇保障性安居工程补助资金分配表', 'year': year, 'stage': stage, 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': out, 'note': '2025和2026仅为提前下达的部分预算，不能与2023、2024年度数据直接比较；2023与2024项目分类不同，具体口径以各年表头为准。预算不是实际支出；注意地区是否包括计划单列市。合并区域为左闭右开坐标。'}
