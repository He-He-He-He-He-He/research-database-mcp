"""中国人民银行调查统计司的年度统计目录和 XLSX 原表。"""
import release_runtime
import io, re
from urllib.parse import urljoin, urlsplit
import requests, openpyxl
BASE = 'https://www.pbc.gov.cn'
HOME = BASE + '/diaochatongjisi/116219/index.html'

def _fetch(url, maxsize=15000000):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > maxsize:
        raise ValueError('响应跳转或文件过大')
    return r.content

def _url(path):
    u = urljoin(BASE, path)
    p = urlsplit(u)
    if p.scheme != 'https' or p.hostname != 'www.pbc.gov.cn' or p.query or p.fragment or ('..' in p.path.split('/')):
        raise ValueError('仅接受人民银行官方 HTTPS 链接')
    return u

def years():
    from bs4 import BeautifulSoup
    s = BeautifulSoup(_fetch(HOME), 'html.parser')
    out = {}
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})年统计数据', title)
        if m and '/116319/' in a['href']:
            u = _url(a['href'])
            out[m.group(1)] = {'year': int(m.group(1)), 'url': u}
    if not out:
        raise ValueError('未识别央行年度统计目录')
    return {'source': '中国人民银行调查统计司', 'items': sorted(out.values(), key=lambda x: x['year'], reverse=True), 'source_url': HOME}

def categories(year):
    from bs4 import BeautifulSoup
    year = int(year)
    item = next((x for x in years()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('年度不在官网目录')
    u = item['url']
    prefix = urlsplit(u).path.rsplit('/index.html', 1)[0] + '/'
    s = BeautifulSoup(_fetch(u), 'html.parser')
    out = {}
    for a in s.select('a[href]'):
        try:
            link = _url(a['href'])
        except ValueError:
            continue
        path = urlsplit(link).path
        text = a.get_text(' ', strip=True)
        if path.startswith(prefix) and path.endswith('/index.html') and (path != prefix + 'index.html') and text:
            out.setdefault(link, {'name': text, 'url': link})
    if not out:
        raise ValueError('无法识别该年分类目录')
    return {'year': year, 'source_url': u, 'items': list(out.values()), 'note': '分类名称随年度变化，需使用该年目录返回的链接。'}

def catalog(year, category_url):
    from bs4 import BeautifulSoup
    if category_url not in {x['url'] for x in categories(year)['items']}:
        raise ValueError('分类不属于所选年度目录')
    s = BeautifulSoup(_fetch(category_url), 'html.parser')
    out = []
    for t in s.select('table.a2015'):
        title = t.select_one('.titp20')
        if not title:
            continue
        links = []
        for a in t.select('a[href]'):
            href = a.get('href', '').strip()
            if not href:
                continue
            try:
                u = _url(href)
            except ValueError:
                continue
            links.append({'label': a.get_text(' ', strip=True), 'url': u})
        out.append({'title': title.get_text(' ', strip=True), 'links': links})
    if not out:
        raise ValueError('未识别此分类原表目录')
    return {'year': int(year), 'source_url': category_url, 'items': out, 'note': '链接可包含 PDF、HTML、XLSX 或季度通报；不同日期版本和表定义可能修订。'}

def workbook(url, sheet=0):
    u = _url(url)
    p = urlsplit(u)
    if not p.path.lower().endswith('.xlsx') or not (p.path.startswith('/diaochatongjisi/') or p.path.startswith('/eportal/')):
        raise ValueError('仅支持央行统计目录官方 XLSX 链接')
    raw = _fetch(u)
    if not raw.startswith(b'PK'):
        raise ValueError('附件不是 XLSX')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=False, data_only=True)
    if isinstance(sheet, bool) or not isinstance(sheet, int) or sheet < 0 or (sheet >= len(w.sheetnames)):
        raise ValueError('工作表序号无效')
    s = w.worksheets[sheet]
    if s.max_row > 1000 or s.max_column > 250:
        raise ValueError('表格过大，请下载原文件查看')
    rows = [[c.value.isoformat() if hasattr(c.value, 'isoformat') else c.value for c in row] for row in s.iter_rows()]
    return {'source': '中国人民银行调查统计司', 'source_url': u, 'sheet_names': w.sheetnames, 'sheet': s.title, 'rows': rows, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'note': '保留工作表原始单元格及合并范围，不推断表头；公式值为文件缓存，空值不等于零。请核对单位、时间范围、说明与修订。'}
