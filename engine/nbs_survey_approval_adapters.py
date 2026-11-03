"""国家统计局部门统计调查审批备案公告。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from women_children_monitor_adapters import _Body
from moe_education_statistics_adapters import _LeafTables
BASE = 'https://www.stats.gov.cn/fw/bmdcxmsp/bmdcspgg/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/fw/bmdcxmsp/bmdcspgg/')) or p.query or p.fragment:
        raise ValueError('仅允许国家统计局审批公告栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def survey_approval_list(page=1, keyword=''):
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
        raise ValueError('未找到审批公告目录，无法确认检索结果')
    return out

def survey_approval_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        sources.append(BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html'))
        for item in survey_approval_list(page):
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '国家统计局部门统计调查审批备案公告', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页标题；目录动态变化，跨页非原子快照，不代表全部历史。审批有效期和后续变化须核最新公告及原始表格。'}

def survey_approval_detail(url):
    html = _get(url)
    p = _Body()
    p.feed(html)
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    t = _LeafTables()
    t.feed(html)
    tables = []
    for x in t.tables:
        if len(x) >= 3 and x not in tables:
            tables.append(x)
    if len(text) < 30 and (not tables):
        raise ValueError('未识别公告正文或表格')
    return {'url': url, 'text': text, 'tables': tables, 'note': '审批备案公告及表格，保留合并单元格；有效期和后续变化以最新国家统计局公告为准。'}
