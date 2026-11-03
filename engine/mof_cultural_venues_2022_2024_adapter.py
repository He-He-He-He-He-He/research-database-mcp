"""财政部公共文化场馆免费开放补助预算原表（不同阶段）。"""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
DATA = {2022: ('https://www.mof.gov.cn/gp/xxgkml/kjs/202111/t20211130_3770587.htm', 'https://www.mof.gov.cn/gp/xxgkml/kjs/202111/P020211130608786126341.xls', '提前下达预算'), 2024: ('https://www.mof.gov.cn/jrttts/202405/t20240508_3934222.htm', 'https://www.mof.gov.cn/jrttts/202405/P020240508334098296924.xls', '年度预算，含提前下达和本次下达')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持2022和2024；2023附件未核实')
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
    return {'source': '财政部公共图书馆、美术馆、文化馆（站）免费开放补助资金预算表', 'year': year, 'stage': stage, 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': out, 'note': '2022仅为提前下达部分，不能与2024年度预算直接比较；2024表同时含场馆数量和预算金额，单位分别是个、万元。预算不是实际支出；注意地区是否包含计划单列市。2025起项目并入公共文化服务体系补助，不能直接作为同口径延续。合并区域为左闭右开坐标。'}
