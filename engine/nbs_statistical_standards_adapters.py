"""国家统计局国家统计标准栏目。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from moe_rules_adapters import _Body
from moe_education_statistics_adapters import _LeafTables
BASE = 'https://www.stats.gov.cn/sj/tjbz/gjtjbz/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/sj/tjbz/gjtjbz/')) or p.query or p.fragment:
        raise ValueError('仅允许国家统计标准栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def statistical_standards(page=1, keyword=''):
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Links()
    p.feed(_get(BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')))
    out = []
    seen = set()
    recognized = False
    for href, title in p.links:
        u = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', u):
            recognized = True
            if keyword in title and u not in seen:
                seen.add(u)
                out.append({'title': title, 'url': u})
    if not recognized:
        raise ValueError('未识别统计标准目录，无法确认检索结果')
    return out

def statistical_standard_detail(url):
    html = _get(url)
    p = _Body()
    p.feed(html)
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    t = _LeafTables()
    t.feed(html)
    tables = []
    for table in t.tables:
        if len(table) >= 3 and table not in tables:
            tables.append(table)
    lines = text.splitlines()
    half = len(lines) // 2
    if half and len(lines) % 2 == 0 and (lines[:half] == lines[half:]):
        text = '\n'.join(lines[:half])
    links = _Links()
    links.feed(html)
    attachments = []
    for href, title in links.links:
        u = urljoin(url, href)
        p = urlparse(u)
        if p.hostname == 'www.stats.gov.cn' and p.path.startswith('/sj/tjbz/gjtjbz/') and re.search('\\.(?:docx?|xlsx?|pdf)$', p.path, re.I):
            attachments.append({'title': title, 'url': u})
    if len(text) < 30:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'tables': tables, 'attachments': attachments, 'note': '正文可能仅含发布令，完整分类须查看附件；版本、实施及后续修改以官方为准。'}
