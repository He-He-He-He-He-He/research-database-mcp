"""Heyuan official social services, townships, trade and tourism yearbook attachments, indexed by edition."""
import release_runtime
import io
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://www.heyuan.gov.cn/zjhy/hygk/hynj/'
CATEGORIES = {'social': 'wjwshqt/', 'township': 'xzzyjjzb/', 'trade': 'mywj/', 'tourism': 'wsly/'}

def _get(url):
    for _ in range(3):
        r = requests.get(url, timeout=30)
        if r.status_code != 404:
            break
    r.raise_for_status()
    return r.content

def _secure(href, base):
    u = urlparse(urljoin(base, href))
    if u.hostname != 'www.heyuan.gov.cn' or u.scheme not in ('http', 'https'):
        raise ValueError('non-official source URL')
    return urlunparse(('https', u.netloc, u.path, u.params, u.query, u.fragment))

def editions(category):
    if category not in CATEGORIES:
        raise ValueError('category must be social, township, trade or tourism')
    url = BASE + CATEGORIES[category]
    soup = BeautifulSoup(_get(url), 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        match = re.search('(\\d{4})年统计年鉴', title)
        if match:
            out.append({'year': int(match.group(1)), 'title': title, 'url': _secure(a['href'], url)})
    if not out:
        raise ValueError('official edition list missing')
    return out

def catalog(category, year):
    matches = [x for x in editions(category) if x['year'] == year]
    if len(matches) != 1:
        raise ValueError('edition missing or ambiguous')
    page = matches[0]['url']
    soup = BeautifulSoup(_get(page), 'html.parser')
    items = []
    for a in soup.select('a.nfw-cms-attachment[href]'):
        title = a.get_text(' ', strip=True)
        url = _secure(a['href'], page)
        if title and urlparse(url).path.lower().endswith(('.xls', '.xlsx')):
            items.append({'title': title, 'url': url})
    if not items:
        raise ValueError('official workbook list missing')
    return items

def workbook(category, year, title):
    matches = [x for x in catalog(category, year) if x['title'] == title]
    if len(matches) != 1:
        raise ValueError('workbook missing or ambiguous')
    item = matches[0]
    raw = _get(item['url'])
    if len(raw) > 8000000:
        raise ValueError('workbook exceeds limit')
    if item['url'].lower().endswith('.xlsx'):
        import openpyxl
        book = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
        sheets = [{'name': s.title, 'rows': [list(row) for row in s.iter_rows(values_only=True)], 'merged_cells': [str(x) for x in s.merged_cells.ranges]} for s in book.worksheets]
    else:
        book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
        sheets = [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': s.merged_cells} for s in book.sheets()]
    return {'source': '河源市统计局', 'edition': year, 'category': category, 'title': title, 'source_url': item['url'], 'sheets': sheets}
