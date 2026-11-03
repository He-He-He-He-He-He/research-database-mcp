"""苏州市政府发布的苏州工业园区主要经济指标。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links, _Tables
BASE = 'https://www.suzhou.gov.cn/szsrmzf/tjsjjd/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.suzhou.gov.cn' or (not p.path.startswith('/szsrmzf/tjsjjd/')):
        raise ValueError('仅允许访问苏州市政府统计数据栏目')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def suzhou_park_list(page=1):
    page = int(page)
    if page < 1 or page > 100:
        raise ValueError('页码超出范围')
    url = urljoin(BASE, 'xxgkzdly.shtml' if page == 1 else f'xxgkzdly_{page - 1}.shtml')
    p = _Links()
    p.feed(_get(url))
    items = []
    for href, title in p.links:
        u = urljoin(BASE, href)
        if '苏州工业园区主要经济统计指标' in title and re.fullmatch('https://www\\.suzhou\\.gov\\.cn/szsrmzf/tjsjjd/\\d{6}/[a-f0-9]+\\.shtml', u):
            items.append({'title': title, 'url': u})
    return items

def suzhou_park_detail(url):
    p = _Tables()
    p.feed(_get(url))
    if not p.tables:
        raise ValueError('未发现 HTML 表格')
    return {'url': url, 'tables': p.tables, 'note': '原始单元格；统计范围为工业园区，各项单位、累计期间及口径以原文为准。'}
