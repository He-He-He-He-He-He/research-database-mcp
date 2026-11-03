"""国务院学位委员会 2026 年自主审核增设学位授予点本地查询。"""
import release_runtime
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2026自主审核增设学位授予点.pdf')
SOURCE_URL = 'https://www.moe.gov.cn/srcsite/A22/yjss_xwgl/moe_818/202610/W020261020378271569479.pdf'
NOTICE_URL = 'https://www.moe.gov.cn/srcsite/A22/yjss_xwgl/moe_818/202610/t20261020_1455259.html'

def search_degree_additions_2026(keyword=''):
    """按学校、代码、学位点名称或类型子串搜索，空关键词返回全部。"""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    blocks = []
    for page_num, page in enumerate(PdfReader(str(PDF_PATH)).pages, 1):
        text = page.extract_text() or ''
        text = re.sub('—\\s*\\d+\\s*—|附件\\s*2|2026\\s*年度学位授予资格自主审核单位增设的|学位授予点名单|序号\\s*单位名称\\s*学位点\\s*代码\\s*学位点名称\\s*学位点类型', '', text)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match('^\\d{1,3}(?:\\s|$)', line):
                blocks.append([page_num, line])
            elif blocks:
                blocks[-1][1] += ' ' + line
    if len(blocks) != 99:
        raise ValueError(f'PDF 解析异常：预期 99 条，实际 {len(blocks)} 条')
    records, school = ([], '')
    for page, raw in blocks:
        match = re.match('^(\\d+)\\s+(?:(\\S+?)\\s+)?(S?\\d{4})\\s+(.+?)\\s+((?:一级学科|交叉学科|硕士专业|博士专业).+)$', raw)
        if not match:
            raise ValueError(f'PDF 原表行无法解析：{raw}')
        number, name, code, discipline, degree_type = match.groups()
        school = name or school
        if int(number) != len(records) + 1 or not school:
            raise ValueError('PDF 顺序或单位名称解析异常')
        records.append({'number': int(number), 'school': school, 'code': code, 'name': discipline, 'degree_type': degree_type, 'outside_catalog': '目录外' in degree_type, 'pdf_page': page, 'source_url': SOURCE_URL, 'notice_url': NOTICE_URL, 'year': 2026, 'action': '增设'})
    keyword = keyword.strip()
    return [r for r in records if not keyword or any((keyword in r[k] for k in ('school', 'code', 'name', 'degree_type')))]
