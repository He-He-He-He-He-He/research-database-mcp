"""国家卫健委 2022—2023 年公报：原 PDF 搜索及表 1。"""
import release_runtime
from pathlib import Path
SOURCES = {2022: 'https://www.gov.cn/lianbo/bumen/202310/P020231012649046990925.pdf', 2023: 'https://www.gov.cn/lianbo/bumen/202408/P020240829729470466631.pdf'}
ROOT = Path(__file__).resolve().parent / '数据' / '国家卫生健康统计公报'

def _document(year):
    try:
        import fitz
    except ImportError as exc:
        raise ImportError('此接口需要 PyMuPDF：pip install PyMuPDF') from exc
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2022、2023 年')
    return (year, fitz.open(ROOT / f'{year}.pdf'))

def nhc_health_search(year, keyword, limit=20):
    if not keyword.strip() or not 1 <= int(limit) <= 100:
        raise ValueError('关键词不能为空，limit 应为 1—100')
    year, doc = _document(year)
    needle = ''.join(keyword.split())
    try:
        result = []
        for i, page in enumerate(doc):
            content = page.get_text()
            if needle in ''.join(content.split()):
                result.append({'year': year, 'pdf_page': i + 1, 'text': content, 'source_url': SOURCES[year]})
                if len(result) >= int(limit):
                    break
        return result
    finally:
        doc.close()

def nhc_health_institutions_table(year):
    """表 1 的原始文本单元格；同一统计年可能在不同版次中修订。"""
    year, doc = _document(year)
    try:
        lines = [x.strip() for x in doc[2].get_text().splitlines() if x.strip()]
    finally:
        doc.close()
    if '全国医疗卫生机构及床位数' not in lines:
        raise ValueError('原表标题不匹配')
    start = lines.index('床位数（张）') + 1
    if lines[start:start + 4] != [str(year - 1), str(year), str(year - 1), str(year)]:
        raise ValueError('原表年份表头不匹配')
    end = next((i for i in range(start + 4, len(lines)) if lines[i].startswith('注：')))
    cells = lines[start + 4:end]
    if len(cells) != 23 * 5 or cells[0] != '总计':
        raise ValueError('原表结构异常，未作猜测解析')
    rows = []
    for i in range(0, len(cells), 5):
        name, a, b, c, d = cells[i:i + 5]
        rows.append({'category': name, 'institutions': {str(year - 1): a, str(year): b}, 'beds': {str(year - 1): c, str(year): d}})
    return {'report_year': year, 'pdf_page': 3, 'source_url': SOURCES[year], 'units': {'institutions': '个', 'beds': '张'}, 'note': '# 系其中数；破折号按原文保留，跨版本同年数据可能不同。', 'rows': rows}
