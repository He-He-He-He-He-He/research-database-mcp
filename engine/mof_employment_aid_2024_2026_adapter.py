"""财政部就业补助资金分地区预算原表。"""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://sbs.mof.gov.cn/zxzyzf/jybzzj/'
DATA = {2024: ('202404/t20240422_3933189.htm', '202404/P020240423360693425651.xls'), 2025: ('202504/t20250424_3962652.htm', '202504/P020250424546620921478.xls'), 2026: ('202604/t20260427_3988462.htm', '202604/P020260427332817123854.xls')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持2024、2025和2026')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('筛选词无效')
    article, path = DATA[year]
    url = BASE + path
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000 or not raw.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('非预期XLS')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = []
    q = ''.join(keyword.split())
    for s in book.sheets():
        if s.nrows > 10000 or s.ncols > 256:
            raise ValueError('表尺寸异常')
        rows = [s.row_values(i) for i in range(s.nrows)]
        for row in rows:
            while row and row[-1] == '':
                row.pop()
        selected = [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if not q or q in ''.join((''.join(str(v).split()) for v in row))]
        sheets.append({'sheet': s.name, 'headers': rows[:6], 'rows': selected, 'merged_cells': [list(x) for x in s.merged_cells]})
    return {'source': '财政部人力资源社会保障部中央财政就业补助资金分配表', 'year': year, 'article_url': BASE + article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': sheets, 'note': '预算分配非实际支出；总分配与已下达及此次下达属于合计与组成，不得重复相加。单位及地区口径以原表为准；单列市是否包含在省份须核对原表。合并区域采用左闭右开坐标。'}
