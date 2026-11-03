"""国家发展改革委国家级专项规划公开目录和正文。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from moe_rules_adapters import _Body
BASE = 'https://www.ndrc.gov.cn/fggz/fzzlgh/gjjzxgh/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.ndrc.gov.cn' or (not p.path.startswith('/fggz/fzzlgh/gjjzxgh/')) or p.query or p.fragment:
        raise ValueError('仅允许国家级专项规划栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def national_special_plans(page=1, keyword=''):
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
        raise ValueError('未识别规划目录，无法确认检索结果')
    return out

def national_special_plan_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别规划正文')
    return {'url': url, 'text': text, 'note': '国家发改委发布的专项规划栏目正文，不代表全部国家政策；实施期限、修订和附件须核对原文。'}
