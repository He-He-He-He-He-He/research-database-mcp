"""福建省统计局社会消费品零售公开数据。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links, _Tables
BASE = 'https://tjj.fujian.gov.cn/xxgk/tjxx/shxfpls/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'tjj.fujian.gov.cn' or (not p.path.startswith('/xxgk/tjxx/shxfpls/')):
        raise ValueError('仅可读取福建统计局社会消费品零售栏目')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def fujian_retail_list(keyword=''):
    parser = _Links()
    parser.feed(_get(BASE))
    items = []
    for href, title in parser.links:
        url = urljoin(BASE, href)
        if re.fullmatch('https://tjj\\.fujian\\.gov\\.cn/xxgk/tjxx/shxfpls/\\d{6}/t\\d{8}_\\d+\\.htm', url) and keyword in title:
            items.append({'title': title, 'url': url})
    if not items and (not keyword):
        raise ValueError('栏目没有读取到详情，可能已改版')
    return items

def fujian_retail_detail(url):
    parser = _Tables()
    parser.feed(_get(url))
    if not parser.tables:
        raise ValueError('此项没有 HTML 表格，可能为文字解读或已改版')
    return {'url': url, 'tables': parser.tables, 'note': '原始单元格；表头、单位及统计口径请对照官方正文。'}
