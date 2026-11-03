"""教育部 2022 年第二轮双一流建设名单；读取随包提供的官方 PDF。"""
import release_runtime
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('教育部第二轮双一流建设名单2022.pdf')
SOURCE_URL = 'https://www.moe.gov.cn/srcsite/A22/s7065/202202/W020220214318455516037.pdf'

def list_double_first_2022(keyword=''):
    """按学校或建设学科子串查询，返回官方原文、学科列表和 PDF 页码。"""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('读取本表需要安装可选依赖 pypdf') from e
    lines = []
    for page_num, page in enumerate(PdfReader(str(PDF_PATH)).pages, 1):
        lines.extend(((page_num, line.strip()) for line in (page.extract_text() or '').splitlines() if line.strip()))
    records = []
    for page_num, line in lines:
        if '：' in line:
            school, content = line.split('：', 1)
            records.append({'school': school, 'original_text': content, 'pages': [page_num]})
        elif records:
            records[-1]['original_text'] += line
            if page_num not in records[-1]['pages']:
                records[-1]['pages'].append(page_num)
    if len(records) != 147:
        raise ValueError(f'PDF 提取结果异常：预期 147 所，实际 {len(records)} 所')
    for item in records:
        raw = re.sub('\\s+', '', item['original_text'])
        item['original_text'] = raw
        item['disciplines'] = [] if raw.startswith('（自主确定') else raw.split('、')
        item['self_determined'] = raw.startswith('（自主确定')
        item['source_url'] = SOURCE_URL
        item['round'] = 2
        item['published_year'] = 2022
    keyword = keyword.strip()
    return [r for r in records if not keyword or keyword in r['school'] or keyword in r['original_text']]
