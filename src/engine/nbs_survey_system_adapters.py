"""国家统计局部门统计调查制度公开说明。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from women_children_monitor_adapters import _Body
BASE = 'https://www.stats.gov.cn/fw/bmdcxmsp/bmzd/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/fw/bmdcxmsp/bmzd/')) or p.query or p.fragment:
        raise ValueError('仅允许国家统计局部门制度栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def survey_system_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Links()
    p.feed(_get(BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')))
    out = []
    seen = set()
    for href, title in p.links:
        u = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', u) and keyword in title and (u not in seen):
            seen.add(u)
            out.append({'title': title, 'url': u})
    if not out and (not keyword):
        raise ValueError('未找到制度目录')
    return out

def survey_system_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '部门统计调查制度说明；调查范围、频率和有效期以原文及最新批准文件为准。'}
