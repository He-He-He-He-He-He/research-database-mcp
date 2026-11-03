"""国家统计局国家统计调查制度目录及其附件链接。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from women_children_monitor_adapters import _Body
BASE = 'https://www.stats.gov.cn/xxgk/tjbzhzd/gjtjdczd/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/xxgk/tjbzhzd/gjtjdczd/')) or p.query or p.fragment:
        raise ValueError('仅允许国家统计调查制度栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def national_survey_list(page=1, keyword=''):
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
        raise ValueError('未识别统计调查制度目录，无法确认检索结果')
    return out

def national_survey_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        sources.append(BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html'))
        for item in national_survey_list(page):
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '国家统计局国家统计调查制度栏目', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页标题，目录动态变化，跨页非原子快照，不代表全部历史。具体调查内容和年份应核原文及附件；附件不在此查询中读取。'}

def national_survey_detail(url):
    html = _get(url)
    p = _Body()
    p.feed(html)
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    l = _Links()
    l.feed(html)
    attachments = []
    for href, title in l.links:
        u = urljoin(url, href)
        x = urlparse(u)
        if x.hostname == 'www.stats.gov.cn' and x.path.startswith('/xxgk/tjbzhzd/gjtjdczd/') and re.search('\\.(?:docx?|pdf|xlsx?)$', x.path, re.I):
            attachments.append({'title': title, 'url': u})
    if not text and (not attachments):
        raise ValueError('未找到正文或附件')
    return {'url': url, 'text': text, 'attachments': attachments, 'note': '此栏目部分正文仅提示附件，接口不解析 DOC；调查年份与具体内容应核对附件。'}
