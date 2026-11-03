"""财政部学生资助补助经费预算通知及附件原表。"""
import release_runtime
import io, re, hashlib
from urllib.parse import urljoin, urlparse
import requests
import openpyxl
from bs4 import BeautifulSoup
INDEX = 'https://jkw.mof.gov.cn/zxzyzf/xszzbzjf/index.htm'
EXTRA_2024 = 'https://jkw.mof.gov.cn/gongzuotongzhi/202405/t20240508_3934243.htm'

def catalog(year):
    if isinstance(year, bool) or year not in range(2021, 2027):
        raise ValueError('年份支持2021—2026')
    r = requests.get(INDEX, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    for a in s.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        href = a['href']
        if f'{year}年学生资助补助经费预算' not in title or '下达' not in title:
            continue
        url = urljoin(INDEX, href)
        if urlparse(url).hostname != 'jkw.mof.gov.cn':
            raise ValueError('目录包含非官方链接')
        items.append({'title': title, 'url': url, 'stage': '提前下达' if '提前下达' in title else '下达'})
    if year == 2024:
        items.append({'title': '关于下达2024年学生资助补助经费预算的通知', 'url': EXTRA_2024, 'stage': '下达'})
    if not items:
        raise ValueError('未找到该年度通知')
    return {'source': '财政部科教和文化司', 'year': year, 'catalog_url': INDEX, 'items': items, 'note': '仅列本栏目当前可见通知及补充核实的2024通知，不保证同年所有批次齐全。'}

def attachments(year, stage='下达'):
    if stage not in ('下达', '提前下达'):
        raise ValueError('stage只能是下达或提前下达')
    items = [x for x in catalog(year)['items'] if x['stage'] == stage]
    if len(items) != 1:
        raise ValueError('该年份阶段未找到或不唯一')
    item = items[0]
    r = requests.get(item['url'], timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        href = a['href'].strip()
        url = urljoin(item['url'], href)
        if not re.search('\\.xlsx$', url, re.I):
            continue
        if urlparse(url).hostname != 'jkw.mof.gov.cn':
            raise ValueError('发现非财政部附件')
        out.append({'title': ' '.join(a.get_text(' ', strip=True).split()), 'url': url})
    if not out:
        raise ValueError('无可用XLSX附件')
    return {'year': year, 'stage': stage, 'article': item, 'attachments': out}

def table(year, stage='下达', attachment_index=0, keyword=''):
    a = attachments(year, stage)
    items = a['attachments']
    if isinstance(attachment_index, bool) or not isinstance(attachment_index, int) or (not 0 <= attachment_index < len(items)):
        raise ValueError('附件索引无效')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('筛选词无效')
    item = items[attachment_index]
    r = requests.get(item['url'], timeout=30)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000 or not raw.startswith(b'PK\x03\x04'):
        raise ValueError('附件非XLSX或过大')
    wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=False)
    sheets = []
    q = ''.join(keyword.split())
    for ws in wb.worksheets:
        if ws.max_row > 10000 or ws.max_column > 100:
            raise ValueError('工作表异常过大')
        rows = [[v if v is None or isinstance(v, (str, int, float, bool)) else str(v) for v in row] for row in ws.iter_rows(values_only=True)]
        matched = [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if q and q in ''.join((''.join(str(c).split()) for c in row if c is not None))]
        sheets.append({'sheet': ws.title, 'headers': rows[:6], 'rows': matched if keyword else [{'row': i, 'cells': row} for i, row in enumerate(rows, 1)], 'merged_ranges': [str(x) for x in ws.merged_cells.ranges]})
    wb.close()
    return {'source': '财政部学生资助补助经费预算附件', 'year': year, 'stage': stage, 'article_url': a['article']['url'], 'attachment': item, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': sheets, 'note': '各批次为预算下达，不是支出决算或学生个体资助额；提前下达与后续下达不一定可简单相加。表格范围、单位、地区合并关系及清算以原文、表头和注释为准。'}
