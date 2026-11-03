"""深圳证券交易所全市场统计月报。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links, _Tables
BASE = 'https://www.szse.cn/market/periodical/month/'

def _get(url):
    p = urlparse(url)
    valid = p.scheme == 'https' and (p.hostname == 'www.szse.cn' and p.path.startswith('/market/periodical/month/') or (p.hostname == 'docs.static.szse.cn' and p.path.startswith('/www/market/periodical/month/')))
    if not valid:
        raise ValueError('仅允许读取深交所统计月报目录和章节')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout

def list_szse_market_months():
    html = _get(urljoin(BASE, 'index.html')).decode('utf-8')
    entries = re.findall("value\\s*:\\s*'([^']+)'\\s*,\\s*text\\s*:\\s*'(\\d{4}-\\d{2})'", html)
    if not entries:
        raise ValueError('官网月报目录结构已变化')
    return [{'month': month, 'url': urljoin(BASE, href)} for href, month in entries]

def szse_market_sections(url):
    parser = _Links()
    parser.feed(_get(url).decode('utf-8'))
    result = []
    for href, title in parser.links:
        p = urlparse(href)
        if p.hostname == 'docs.static.szse.cn' and p.path.startswith('/www/market/periodical/month/') and p.path.endswith('.html'):
            result.append({'title': title, 'url': 'https://docs.static.szse.cn' + p.path})
    if not result:
        raise ValueError('没有找到月报章节')
    return result

def szse_market_table(url):
    parser = _Tables()
    parser.feed(_get(url).decode('gb18030'))
    if not parser.tables:
        raise ValueError('没有找到 HTML 表格')
    return {'url': url, 'tables': parser.tables, 'note': '原始行列；请核对表头、单位、合并单元格与官方统计口径。'}
