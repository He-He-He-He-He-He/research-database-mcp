"""2024 年度普通高校本科专业备案与审批结果（增设与调整）。"""
import release_runtime
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2024年度本科专业备案和审批结果.pdf')
SOURCE_URL = 'https://www.moe.gov.cn/srcsite/A08/moe_1034/s4930/202504/W020250422312780758186.pdf'
NOTICE_URL = 'https://www.moe.gov.cn/srcsite/A08/moe_1034/s4930/202504/t20250422_1188239.html'

def search_undergraduate_changes_2024(keyword=''):
    """按学校、专业或专业代码子串查询官方备案审批表。"""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    pattern = re.compile('^(\\d{1,4})\\s+(.+?)\\s+(.+?)\\s+(\\d{6,7}[A-Z]*)\\s+(\\S+)\\s+([一二三四五六七八]年)(?:\\s+(.+))?$')
    records, pending, pending_page = ([], '', None)
    for page_num, page in enumerate(PdfReader(str(PDF_PATH)).pages, 1):
        for line in (page.extract_text() or '').splitlines():
            line = line.strip()
            if records and records[-1]['note'] in ('调整修业', '调整学位'):
                expected = {'调整修业': '年限', '调整学位': '授予门类'}[records[-1]['note']]
                if line != expected:
                    raise ValueError('PDF 备注续行解析异常')
                records[-1]['note'] += line
                continue
            if re.match('^\\d{1,4}\\s+', line):
                if pending:
                    raise ValueError(f'上一条 PDF 行无法解析：{pending}')
                pending, pending_page = (line, page_num)
            elif pending:
                pending += line
            else:
                continue
            match = pattern.match(pending)
            if match:
                number, school, name, code, degree, years, note = match.groups()
                if int(number) != len(records) + 1:
                    raise ValueError('PDF 表格序号不连续')
                records.append({'number': int(number), 'school': school, 'name': name, 'code': code, 'degree': degree, 'duration': years, 'note': note or '', 'pdf_page': pending_page, 'source_url': SOURCE_URL, 'notice_url': NOTICE_URL, 'year': 2024})
                pending = ''
    if pending or len(records) != 1996 or records[-1]['note'] in ('调整修业', '调整学位'):
        raise ValueError('PDF 行数或结尾解析异常')
    keyword = keyword.strip()
    return [r for r in records if not keyword or any((keyword in r[k] for k in ('school', 'name', 'code', 'note')))]
