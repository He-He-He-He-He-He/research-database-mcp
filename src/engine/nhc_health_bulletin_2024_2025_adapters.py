"""2024—2025 年国家卫生健康事业公报及表 1。"""
import release_runtime
from pathlib import Path
SOURCES = {2024: 'https://www.hunan.gov.cn/zqt/zcsd/202512/33861143/files/e9a82e1537784edd8f3e32760d93fb4d.pdf', 2025: 'https://www.hunan.gov.cn/zqt/zcsd/202609/34058125/files/da2b514d479c4984a3acc22e93ed7f8b.pdf'}
ROOT = Path(__file__).resolve().parent / '数据' / '国家卫生健康统计公报'

def _document(year):
    try:
        import fitz
    except ImportError as exc:
        raise ImportError('此接口需要 PyMuPDF：pip install PyMuPDF') from exc
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2024、2025 年')
    return (year, fitz.open(ROOT / f'{year}.pdf'))

def nhc_health_recent_search(year, keyword, limit=20):
    if not keyword.strip() or not 1 <= int(limit) <= 100:
        raise ValueError('关键词不能为空，limit 应为 1—100')
    year, doc = _document(year)
    needle = ''.join(keyword.split())
    try:
        rows = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if needle in ''.join(text.split()):
                rows.append({'year': year, 'pdf_page': i + 1, 'text': text, 'source_url': SOURCES[year]})
                if len(rows) >= int(limit):
                    break
        return rows
    finally:
        doc.close()

def nhc_health_recent_institutions_table(year):
    year, doc = _document(year)
    try:
        pages = [doc[i].get_text() for i in ([1, 2] if year == 2024 else [2])]
    finally:
        doc.close()
    lines = [s.strip() for s in pages[0].splitlines() if s.strip()]
    title = '全国医疗卫生机构及床位数' if year == 2024 else '全国医疗卫生机构数及床位数'
    if title not in lines:
        raise ValueError('原表标题不匹配')
    header = ['机构类别', '机构数（个）', '床位数（张）', str(year - 1), str(year), str(year - 1), str(year)]
    idx = lines.index(title) + 1
    if lines[idx:idx + 7] != header:
        raise ValueError('原表表头不匹配')
    cells = lines[idx + 7:]
    if year == 2024:
        continuation = [s.strip() for s in pages[1].splitlines() if s.strip()]
        if continuation[:7] != header:
            raise ValueError('续页表头不匹配')
        cells += continuation[7:]
    end = next((i for i, s in enumerate(cells) if s.startswith('注：')))
    cells = cells[:end]
    if len(cells) != (22 if year == 2024 else 21) * 5 or cells[0] != '总计':
        raise ValueError('原表结构异常，未作猜测解析')
    rows = []
    for i in range(0, len(cells), 5):
        name, a, b, c, d = cells[i:i + 5]
        rows.append({'category': name, 'institutions': {str(year - 1): a, str(year): b}, 'beds': {str(year - 1): c, str(year): d}})
    return {'report_year': year, 'pdf_pages': [2, 3] if year == 2024 else [3], 'source_url': SOURCES[year], 'units': {'institutions': '个', 'beds': '张'}, 'note': '# 系其中数；破折号按原文保留，统计分类及版本差异请核对原文。', 'rows': rows}
