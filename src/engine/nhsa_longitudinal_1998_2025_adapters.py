"""国家医保局 1998—2025 年经济、人口、卫生、医保数据原表。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('1998至2025年经济人口卫生医保相关数据.pdf')
SOURCE_URL = 'https://www.nhsa.gov.cn/art/2026/7/6/art_257_21309.html'
PDF_URL = 'https://www.nhsa.gov.cn/module/download/downfile.jsp?classid=0&filename=67ba90cfbab14dbe816482fda8ce4758.pdf'

@lru_cache(maxsize=1)
def _read():
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 PyMuPDF') from e
    with fitz.open(str(PDF_PATH)) as doc:
        if len(doc) != 1:
            raise ValueError('原表页数异常')
        words = doc[0].get_text('words')
    headers = [w for w in words if w[5] == 1 and re.fullmatch('\\d{4}', w[4])]
    year_x = {int(w[4]): (w[0] + w[2]) / 2 for w in headers}
    if set(year_x) != set(range(1998, 2026)):
        raise ValueError('表头年份解析异常')
    records = []
    for block in range(2, 17):
        row = [w for w in words if w[5] == block]
        label = ''.join((w[4] for w in row if w[0] < 130)).strip()
        if not label:
            raise ValueError('指标名称缺失')
        unit_match = re.search('[（(]([^（）()]+)[）)]$', label)
        indicator = label[:unit_match.start()] if unit_match else label
        unit = unit_match.group(1) if unit_match else None
        values = {}
        for w in (w for w in row if w[0] >= 130):
            value = w[4].strip()
            if not re.fullmatch('-?\\d+(?:\\.\\d+)?', value):
                raise ValueError(f'无法识别的数值：{value}')
            x = (w[0] + w[2]) / 2
            year = min(year_x, key=lambda y: abs(year_x[y] - x))
            if abs(year_x[year] - x) > 9 or year in values:
                raise ValueError('原表列坐标冲突，请核对 PDF')
            values[year] = value
        for year in sorted(year_x):
            records.append({'year': year, 'indicator': indicator, 'unit': unit, 'value': values.get(year), 'source_url': SOURCE_URL, 'pdf_url': PDF_URL, 'pdf_page': 1})
    if len(records) != 15 * 28:
        raise ValueError('原表行数异常')
    return tuple(records)

def nhsa_longitudinal_1998_2025(year=None, keyword=''):
    """按年份与指标子串查询；原表空白保留为 None。"""
    if year is not None and (not isinstance(year, int) or isinstance(year, bool) or year not in range(1998, 2026)):
        raise ValueError('year 应为 1998 至 2025 的整数')
    keyword = keyword.strip()
    return [dict(r) for r in _read() if (year is None or r['year'] == year) and (not keyword or keyword in r['indicator'])]
