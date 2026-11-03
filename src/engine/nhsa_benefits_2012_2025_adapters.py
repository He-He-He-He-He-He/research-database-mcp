"""国家医保局 2012—2025 年医保待遇享受相关数据原表。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2012至2025年医保待遇享受相关数据.pdf')
SOURCE_URL = 'https://www.nhsa.gov.cn/art/2026/7/13/art_257_21405.html'
PDF_URL = 'https://www.nhsa.gov.cn/module/download/downfile.jsp?classid=0&filename=ed003b38c92c4d0dae9213a5d748f486.pdf'

@lru_cache(maxsize=1)
def _read():
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 PyMuPDF') from e
    records = []
    with fitz.open(str(PDF_PATH)) as doc:
        if len(doc) != 2:
            raise ValueError('原表页数异常')
        for page_no, page in enumerate(doc, 1):
            words = page.get_text('words')
            headers = [w for w in words if w[5] == 2 and re.fullmatch('\\d{4}年', w[4])]
            years = {int(w[4][:-1]): (w[0] + w[2]) / 2 for w in headers}
            if set(years) != set(range(2012, 2026)):
                raise ValueError('表头年份异常')
            for block in range(3, 19 if page_no == 1 else 23):
                row = [w for w in words if w[5] == block]
                label = ''.join((w[4] for w in row if w[0] < 215)).strip()
                if not label:
                    raise ValueError('指标名称缺失')
                if page_no == 1:
                    unit = '万人次'
                elif '参保人数' in label:
                    unit = '万人'
                elif '人次' in label:
                    unit = '万人次'
                else:
                    unit = '亿元'
                values = {}
                for w in (w for w in row if w[0] >= 215):
                    v = w[4].strip()
                    if not re.fullmatch('-?\\d+(?:\\.\\d+)?', v):
                        raise ValueError(f'无法识别的数值: {v}')
                    x = (w[0] + w[2]) / 2
                    y = min(years, key=lambda n: abs(years[n] - x))
                    if abs(years[y] - x) > 14 or y in values:
                        raise ValueError('年份列坐标冲突')
                    values[y] = v
                for y in sorted(years):
                    records.append({'year': y, 'indicator': label, 'value': values.get(y), 'unit': unit, 'unit_basis': '页标题' if page_no == 1 else '按指标名称及页标题判定', 'source_url': SOURCE_URL, 'pdf_url': PDF_URL, 'pdf_page': page_no})
    if len(records) != 36 * 14:
        raise ValueError('表格行数异常')
    return tuple(records)

def nhsa_benefits_2012_2025(year=None, keyword=''):
    """按年份和指标子串搜索，空白返回 None。"""
    if year is not None and (not isinstance(year, int) or isinstance(year, bool) or year not in range(2012, 2026)):
        raise ValueError('year 应为 2012 至 2025 的整数')
    keyword = keyword.strip()
    return [dict(r) for r in _read() if (year is None or r['year'] == year) and (not keyword or keyword in r['indicator'])]
