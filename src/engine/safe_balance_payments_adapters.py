"""国家外汇管理局国际收支平衡表 BPM6 动态原表。"""
import release_runtime
import hashlib
import re
import subprocess
from io import BytesIO
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from openpyxl import load_workbook
LANDING = 'https://www.safe.gov.cn/safe/2019/0627/13519.html'

def _get(url):
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '40', '--max-filesize', '20000000', url], capture_output=True, timeout=45)
    if p.returncode:
        raise RuntimeError('外汇局请求失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 20000000:
        raise RuntimeError('响应超过 20 MB')
    return p.stdout

def load_table(frequency='年度', currency='美元', keyword=''):
    """按频率、计价货币选表，保留原表行号、标题、时点及原始值。"""
    if frequency not in ('年度', '季度') or currency not in ('人民币', '美元', 'SDR'):
        raise ValueError('频率为年度/季度，计价为人民币/美元/SDR')
    soup = BeautifulSoup(_get(LANDING), 'html.parser')
    links = [a for a in soup.select('#content a[href]') if '.xlsx' in a['href'].lower()]
    if len(links) != 1:
        raise RuntimeError('未识别唯一工作簿，来源网页结构可能变化')
    source = urljoin(LANDING, links[0]['href'])
    if not source.startswith('https://www.safe.gov.cn/'):
        raise RuntimeError('原表链接不是预期的外汇局 HTTPS 域名')
    raw = _get(source)
    book = load_workbook(BytesIO(raw), data_only=True, read_only=True)
    found = [s for s in book if s.title.strip().startswith(frequency + 'BOP（' + currency)]
    if len(found) != 1:
        raise RuntimeError('未识别计价工作表')
    sh = found[0]
    headers = [c.value for c in sh[4]]
    columns = [(i, str(v)) for i, v in enumerate(headers[1:], 2) if isinstance(v, int) and 1900 <= v <= 2100 or (isinstance(v, str) and re.fullmatch('\\d{4}Q[1-4]', v))]
    if not columns:
        raise RuntimeError('未识别时间表头')
    notes = []
    rows = []
    in_notes = False
    for idx, values in enumerate(sh.iter_rows(min_row=6, values_only=True), 6):
        name = values[0] if values else None
        if not isinstance(name, str) or not name.strip():
            continue
        if name.strip().startswith('备注'):
            in_notes = True
            continue
        if in_notes:
            notes.append(name.strip())
            continue
        if keyword and keyword not in name:
            continue
        rows.append({'row': idx, 'item': name.strip(), 'values': {year: values[i - 1] if i - 1 < len(values) else None for i, year in columns}})
    return {'source_page': LANDING, 'workbook_url': source, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheet': sh.title.strip(), 'unit': sh.cell(3, 1).value, 'periods': [year for _, year in columns], 'notes': notes, 'rows': rows}
