"""教育部各地教育统计表。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from moe_education_statistics_adapters import _LeafTables
from szse_chinext_adapters import _Links
ROOT = 'https://www.moe.gov.cn/jyb_sjzl/moe_560/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.moe.gov.cn' or (not p.path.startswith('/jyb_sjzl/moe_560/')) or ('/gedi/' not in p.path):
        raise ValueError('仅允许教育部各地教育统计栏目')
    args = ['curl', '--location', '--max-redirs', '3', '--proto-redir', '=http,https', '--fail', '--silent', '--show-error', '--max-time', '20', url]
    return release_runtime.run(args, check=True, capture_output=True).stdout.decode('utf-8')

def moe_region_list(year=2024, page=1):
    year = int(year)
    page = int(page)
    if not 2000 <= year <= 2100 or not 1 <= page <= 100:
        raise ValueError('年份或页码超出范围')
    base = f'{ROOT}{year}/gedi/'
    p = _Links()
    p.feed(_get(base if page == 1 else urljoin(base, f'index_{page - 1}.html')))
    rows = []
    for href, title in p.links:
        url = urljoin(base, href)
        if re.fullmatch(re.escape(base) + '\\d{6}/t\\d{8}_\\d+\\.html', url) and title:
            rows.append({'title': title, 'url': url})
    if not rows:
        raise ValueError('未找到数据目录')
    return rows

def moe_region_detail(url):
    p = _LeafTables()
    p.feed(_get(url))
    if not p.tables:
        raise ValueError('未找到表格')
    return {'url': url, 'tables': p.tables, 'note': '只返回叶级表格，合并单元格属性保留；数据年份与分类统计范围以原表为准。'}
