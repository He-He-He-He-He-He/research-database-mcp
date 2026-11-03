"""财政部城乡医疗救助补助资金预算原表。"""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
DATA = {2024: ('https://sbs.mof.gov.cn/ybxzyzf/cxjmylbxzyzf/202406/t20240613_3937068.htm', 'https://sbs.mof.gov.cn/ybxzyzf/cxjmylbxzyzf/202406/P020241119595100134189.xls', '年度分配'), 2025: ('https://sbs.mof.gov.cn/ybxzyzf/cxjmylbxzyzf/202505/t20250509_3963495.htm', 'https://sbs.mof.gov.cn/ybxzyzf/cxjmylbxzyzf/202505/P020250509644259717362.xls', '年度分配')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持2024和2025')
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
    return {'source': '财政部国家医保局中央财政医疗救助补助资金城乡医疗救助部分分配表', 'year': year, 'stage': stage, 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': out, 'note': '预算不是实际支出，单位万元；2024浙江为包含宁波的合计及其中项，2025浙江为不含宁波的单列项，不能直接比较；各地区及下设其中行不得重复加总，负数为当次预算调整，不能当缺失值。合并区域为左闭右开坐标。'}
