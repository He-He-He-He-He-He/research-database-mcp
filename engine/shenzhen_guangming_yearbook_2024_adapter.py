"""Shenzhen Guangming District official 2024 statistical yearbook XLS workbooks."""
import release_runtime
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
INDEX = 'https://www.szgm.gov.cn/gmtjj/gkmlpt/content/12/12219/post_12219359.html'

def _get(url):
    return release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', url], capture_output=True, check=True, timeout=35).stdout

def catalog(keyword=''):
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        url = urljoin(INDEX, a['href'])
        u = urlparse(url)
        if u.scheme == 'https' and u.hostname == 'www.szgm.gov.cn' and u.path.startswith('/gmtjj/attachment/') and u.path.lower().endswith('.xls') and (keyword in title):
            items.append({'title': title, 'url': url})
    if not items and (not keyword):
        raise ValueError('official catalog missing')
    return items

def workbook(title):
    matches = [x for x in catalog() if x['title'] == title]
    if len(matches) != 1:
        raise ValueError('workbook missing or ambiguous')
    item = matches[0]
    raw = _get(item['url'])
    if len(raw) > 8000000:
        raise ValueError('workbook exceeds size limit')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': s.merged_cells} for s in book.sheets()]
    return {'source': '深圳市光明区统计局《光明区统计年鉴2024》', 'source_url': item['url'], 'catalog_url': INDEX, 'title': title, 'sheets': sheets}
