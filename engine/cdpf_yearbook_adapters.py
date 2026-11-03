"""中国残联公开的年度残疾人事业统计表。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from moe_education_statistics_adapters import _LeafTables
from szse_chinext_adapters import _Links
INDEX = 'https://www.cdpf.org.cn/ndsj11/index.htm'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cdpf.org.cn' or (not (p.path == '/ndsj11/index.htm' or p.path.startswith('/zwgk/zccx/ndsj/zhsjtj/'))):
        raise ValueError('仅允许中国残联年度统计栏目')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def disability_yearbooks():
    parser = _Links()
    parser.feed(_get(INDEX))
    rows = []
    for href, title in parser.links:
        url = urljoin(INDEX, href)
        if re.fullmatch('https://www\\.cdpf\\.org\\.cn/zwgk/zccx/ndsj/zhsjtj/\\d+zh/[a-f0-9]+\\.htm', url) and '中国残疾人事业统计年鉴' in title:
            rows.append({'title': title, 'url': url})
    if not rows:
        raise ValueError('未找到年鉴目录')
    return rows

def disability_yearbook_table(url):
    p = _LeafTables()
    p.feed(_get(url))
    tables = [x for x in p.tables if len(x) >= 3]
    if not tables:
        raise ValueError('没有找到统计表')
    return {'url': url, 'tables': tables, 'note': '按表格原始文字和合并单元格属性返回；年鉴出版年与数据年可能不同，指标、单位与口径以原表为准。'}
