"""中国民航局历年机场生产公报和吞吐量原始表查询。"""
import release_runtime
import hashlib, io, re, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests, openpyxl
from bs4 import BeautifulSoup
BASE = 'https://www.caac.gov.cn/XXGK/XXGK/TJSJ/'
INDEX = BASE + 'index_1216.html'

def _get(url, cap=10000000):
    with requests.get(url, timeout=(15, 35), allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源发生重定向')
        out = bytearray()
        for chunk in r.iter_content(65536):
            out.extend(chunk)
            if len(out) > cap:
                raise ValueError('来源超出大小上限')
        return bytes(out)

def catalog():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    out = {}
    for a in soup.select('a[href]'):
        title = (a.get('title') or a.get_text(' ', strip=True)).strip()
        m = re.fullmatch('(20\\d{2})年(?:全国民用运输机场|民航机场|全国机场)生产统计公报', title)
        url = urljoin(INDEX, a['href'])
        p = urlsplit(url)
        if m and p.scheme == 'https' and (p.hostname == 'www.caac.gov.cn') and re.fullmatch('/XXGK/XXGK/TJSJ/\\d{6}/t\\d{8}_\\d+\\.html', p.path):
            out[int(m[1])] = {'year': int(m[1]), 'title': title, 'url': url}
    if not out:
        raise ValueError('未识别官方目录')
    return {'source': '中国民航局机场生产统计公报', 'source_url': INDEX, 'items': sorted(out.values(), key=lambda x: x['year'], reverse=True), 'note': '历史目录；每年附件格式及实际可访问性可能变化。'}

def attachments(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year 必须为整数')
    item = next((x for x in catalog()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('年份不在目录中')
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        url = urljoin(item['url'], a['href'])
        p = urlsplit(url)
        if p.scheme == 'https' and p.hostname == 'www.caac.gov.cn' and re.fullmatch('/XXGK/XXGK/TJSJ/\\d{6}/P\\d+\\.xlsx?', p.path, re.I):
            out.append({'title': title, 'url': url, 'format': p.path.rsplit('.', 1)[-1].lower()})
    return {'source': '中国民航局机场生产统计公报', **item, 'attachments': out, 'note': '仅列公报页中的电子表格；没有附件不等于没有公报。'}

def rows(year, keyword='', attachment_index=0, sheet_index=0, limit=100):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    for name, v, upper in [('attachment_index', attachment_index, 100), ('sheet_index', sheet_index, 100), ('limit', limit, 500)]:
        if isinstance(v, bool) or not isinstance(v, int) or v < (1 if name == 'limit' else 0) or (v > upper):
            raise ValueError(name + ' 越界')
    details = attachments(year)
    items = details['attachments']
    if attachment_index >= len(items):
        raise ValueError('附件索引越界或无电子表格')
    att = items[attachment_index]
    raw = _get(att['url'])
    sha = hashlib.sha256(raw).hexdigest()
    if att['format'] == 'xlsx':
        if not raw.startswith(b'PK\x03\x04'):
            raise ValueError('不是 XLSX')
        book = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        names = book.sheetnames
        if sheet_index >= len(names):
            raise ValueError('工作表索引越界')
        sh = book[names[sheet_index]]
        if sh.max_row > 10000 or sh.max_column > 100:
            raise ValueError('工作表尺寸超限')
        values = [list(row) for row in sh.iter_rows(values_only=True)]
    else:
        if not raw.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            raise ValueError('不是 XLS')
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        import xlrd
        book = xlrd.open_workbook(file_contents=raw)
        names = book.sheet_names()
        if sheet_index >= len(names):
            raise ValueError('工作表索引越界')
        sh = book.sheet_by_index(sheet_index)
        if sh.nrows > 10000 or sh.ncols > 100:
            raise ValueError('工作表尺寸超限')
        values = [sh.row_values(i) for i in range(sh.nrows)]
    hits = [{'row': i + 1, 'cells': row} for i, row in enumerate(values) if keyword in ' '.join((str(v) for v in row if v is not None))]
    return {'source': '中国民航局机场生产统计公报', 'year': year, 'report_url': details['url'], 'attachment': att, 'sha256': sha, 'sheet_names': names, 'sheet_index': sheet_index, 'header_rows': [{'row': i + 1, 'cells': v} for i, v in enumerate(values[:5])], 'matched_rows': len(hits), 'rows': hits[:limit], 'note': '原始表格行、列和多级表头保留；未填充合并单元格，空值不等于零。机场统计口径、单位、同比与排名须核对应年度表头及公报。'}
