"""国家能源局河南监管办公开电力供需通报目录与原表。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://henb.nea.gov.cn/dtyw/sjfd/'

def _get(url):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 8000000:
        raise ValueError('网页跳转或响应过大')
    r.encoding = 'utf-8'
    return BeautifulSoup(r.text, 'html.parser')

def _valid_url(url):
    p = urlsplit(url)
    return p.scheme == 'https' and p.hostname == 'henb.nea.gov.cn' and (not p.query) and (not p.fragment) and re.fullmatch('/dtyw/sjfd/\\d{6}/t\\d{8}_\\d+\\.html', p.path)

def catalog(page=1, keyword=''):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码须在 1–100 之间')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多100字')
    url = BASE + ('index.html' if page == 1 else f'index_{page - 1}.html')
    s = _get(url)
    items = []
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        link = urljoin(url, a['href'])
        if '电力供需' not in title or keyword not in title or (not _valid_url(link)):
            continue
        items.append({'title': title, 'url': link})
    return {'source': '国家能源局河南监管办公室', 'source_url': url, 'page': page, 'keyword': keyword, 'items': items, 'note': '只筛选当前页中标题含电力供需的报告；动态更新可能导致分页变化，不代表已搜索全部历史。'}

def report(url):
    if not isinstance(url, str) or not _valid_url(url):
        raise ValueError('仅接受本栏目官方报告链接')
    s = _get(url)
    body = s.select_one('.TRS_UEDITOR') or s.select_one('.wrapper_detail_text')
    if not body:
        raise ValueError('未识别报告正文')
    tables = []
    for table in body.select('table'):
        rows = []
        for tr in table.select('tr'):
            cells = []
            for cell in tr.find_all(['td', 'th'], recursive=False):
                cells.append({'text': cell.get_text(' ', strip=True), 'rowspan': int(cell.get('rowspan', 1)), 'colspan': int(cell.get('colspan', 1))})
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('没有可识别 HTML 表格；请查看原报告')
    paras = [p.get_text(' ', strip=True) for p in body.find_all('p') if p.get_text(' ', strip=True) and (not p.find_parent('table'))]
    return {'source': '国家能源局河南监管办公室', 'source_url': url, 'paragraphs': paras, 'tables': tables, 'note': '原表保留合并单元格，未推断表头；单位及范围以各表标题和正文说明为准；同比增速不等于环比。'}
