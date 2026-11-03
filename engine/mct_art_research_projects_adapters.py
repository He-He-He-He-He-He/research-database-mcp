"""国家社科基金艺术学 2024、2025 年度项目官方 PDF。"""
import release_runtime
import re
from pathlib import Path
from contextlib import redirect_stdout
import sys
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2024: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202409/P020240910571499181989.pdf', 255), 2025: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202509/P020250904330108217710.pdf', 285)}

def mct_art_research_projects(year, keyword=''):
    """按项目名称、单位、负责人或批准号筛选已公布年度立项表。"""
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2024、2025 年度')
    try:
        import fitz
    except ImportError as exc:
        raise ImportError('需要 PyMuPDF：pip install PyMuPDF') from exc
    source, expected = SOURCES[year]
    doc = fitz.open(ROOT / f'{year}.pdf')
    rows = []
    try:
        for i, page in enumerate(doc):
            with redirect_stdout(sys.stderr):
                tables = page.find_tables().tables
            if len(tables) != 1:
                raise ValueError(f'第 {i + 1} 页表格结构异常')
            for cells in tables[0].extract():
                if not cells or '批准号' in str(cells[0]):
                    continue
                if len(cells) != 5 or not re.fullmatch('\\d\\d[A-Z]{2}\\d{3}', str(cells[0] or '').strip()):
                    raise ValueError(f'第 {i + 1} 页发现未识别行')
                rows.append({'year': year, '批准号': cells[0], '项目名称': cells[1], '负责人': cells[2], '责任单位': cells[3], '项目类别': cells[4], 'pdf_page': i + 1, 'source_url': source})
    finally:
        doc.close()
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('行数或批准号不符合已核验原表')
    needle = ''.join(keyword.split()).casefold()
    return [r for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
