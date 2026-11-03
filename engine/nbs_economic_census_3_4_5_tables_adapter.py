"""National Bureau of Statistics 3rd–5th economic censuses: official XLS catalog."""
import release_runtime
import hashlib, re, sys
from pathlib import Path
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://www.stats.gov.cn/sj/pcsj/jjpc/'
YEARS = {2013: '3jp', 2018: '4jp', 2023: '5jp'}
PATH = re.compile('(?:html|excel)/[A-Za-z0-9_.-]+ ?\\.xls', re.I)

def _valid_path(value):
    return isinstance(value, str) and '..' not in value and bool(PATH.fullmatch(value))

def _get(url, limit):
    with requests.get(url, stream=True, timeout=(10, 45), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > limit:
                raise ValueError('response too large')
    return bytes(data)

def catalog(year, keyword=''):
    if type(year) is not int or year not in YEARS:
        raise ValueError('census year must be 2013, 2018, or 2023')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    base = BASE + YEARS[year] + '/zk/'
    soup = BeautifulSoup(_get(base + 'lefte.htm', 4000000), 'html.parser')
    out = []
    for a in soup.find_all('a', href=True):
        path = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if _valid_path(path) and title and (keyword in title):
            out.append({'id': path, 'title': title, 'url': urljoin(base, quote(path, safe='/'))})
    if not out and (not keyword):
        raise ValueError('official catalog not recognized')
    return {'source': f'国家统计局{year}年全国经济普查资料', 'year': year, 'catalog_url': base + 'lefte.htm', 'count': len(out), 'items': out, 'note': '列官方目录中的XLS链接；列出不代表每个链接均已验证，下载时校验内容。统计范围和年际可比性以各原表和说明为准。'}

def table(year, table_id):
    if not _valid_path(table_id):
        raise ValueError('invalid table_id')
    items = catalog(year)['items']
    matches = [x for x in items if x['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('table id missing or ambiguous in official catalog')
    item = matches[0]
    raw = _get(item['url'], 15000000)
    if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('source is not XLS')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = []
    for sheet in book.sheets():
        if sheet.nrows * sheet.ncols > 1000000:
            raise ValueError('table too large')
        sheets.append({'name': sheet.name, 'rows': [sheet.row_values(i) for i in range(sheet.nrows)], 'merged_cells': [list(r) for r in sheet.merged_cells]})
    return {'source': f'国家统计局{year}年全国经济普查资料', 'year': year, 'title': item['title'], 'source_url': item['url'], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'sheets': sheets, 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]', 'note': '按原Excel工作表返回单元格和合并坐标；年份、指标定义与范围随各次普查不同，使用前须查表头和说明，不直接拼接。'}
