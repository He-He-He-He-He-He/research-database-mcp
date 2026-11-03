"""财政部城乡义务教育补助经费分地区预算表。"""
import release_runtime
import hashlib, sys
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
DATA = {2022: ('https://jkw.mof.gov.cn/gongzuotongzhi/202205/t20220509_3808973.htm', 'https://jkw.mof.gov.cn/gongzuotongzhi/202205/P020220512336851532855.xls'), 2023: ('https://jkw.mof.gov.cn/gongzuotongzhi/202305/t20230519_3885582.htm', 'https://jkw.mof.gov.cn/gongzuotongzhi/202305/P020230519530845902534.xls'), 2024: ('https://jkw.mof.gov.cn/gongzuotongzhi/202405/t20240510_3934513.htm', 'https://jkw.mof.gov.cn/gongzuotongzhi/202405/P020240510585258538295.xls'), 2026: ('https://jkw.mof.gov.cn/ybxzyzf/cxywjybzjf/202604/t20260429_3988826.htm', 'https://jkw.mof.gov.cn/ybxzyzf/cxywjybzjf/202604/P020260429606078140752.xls')}

def table(year, keyword=''):
    if isinstance(year, bool) or year not in DATA:
        raise ValueError('支持2022、2023、2024和2026；2025附件待核验')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('筛选词无效')
    article, url = DATA[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000 or not raw.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('附件非预期XLS')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = []
    q = ''.join(keyword.split())
    for ws in book.sheets():
        if ws.nrows > 10000 or ws.ncols > 256:
            raise ValueError('表格尺寸异常')
        rows = [ws.row_values(i) for i in range(ws.nrows)]
        for row in rows:
            while row and row[-1] == '':
                row.pop()
        matched = [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if q and q in ''.join((''.join(str(c).split()) for c in row))]
        sheets.append({'sheet': ws.name, 'headers': rows[:6], 'rows': matched if keyword else [{'row': i, 'cells': row} for i, row in enumerate(rows, 1)], 'merged_cells': [list(x) for x in ws.merged_cells]})
    return {'source': '财政部、教育部城乡义务教育补助经费预算表', 'year': year, 'article_url': article, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': sheets, 'note': '单位以原表为准；保留预算、提前下达和本次下达的不同列，不是支出决算。省级行是否包括计划单列市以原表标注为准，避免重复相加。合并区域为左闭右开索引。'}
