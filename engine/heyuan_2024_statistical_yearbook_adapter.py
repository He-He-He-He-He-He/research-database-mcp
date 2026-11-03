"""Heyuan 2024 yearbook: official downloadable XLS source tables."""
import release_runtime
import requests
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
sys.path.insert(0, str(Path(__file__).resolve().parent / '.vendor'))
PAGE = 'https://www.heyuan.gov.cn/zjhy/hygk/hynj/zhrkhs/content/mpost_635766.html'

def _get(url, timeout):
    for _ in range(3):
        r = requests.get(url, timeout=timeout)
        if r.status_code != 404:
            break
    r.raise_for_status()
    return r

def catalog():
    r = _get(PAGE, 20)
    r.encoding = 'utf8'
    soup = BeautifulSoup(r.text, 'html.parser')
    out = []
    for a in soup.select('a.nfw-cms-attachment'):
        u = a.get('href', '').replace('http://www.heyuan.gov.cn/', 'https://www.heyuan.gov.cn/')
        if urlparse(u).hostname == 'www.heyuan.gov.cn' and u.endswith('.xls'):
            out.append({'title': a.get_text(strip=True), 'url': u, 'attachment_id': a.get('attachment-id')})
    if not out:
        raise RuntimeError('未发现年鉴附件，页面可能改版')
    return out

def _workbook(attachment_id):
    try:
        import xlrd
    except ImportError:
        raise RuntimeError('读取 XLS 需要安装 xlrd') from None
    choices = [x for x in catalog() if x['attachment_id'] == str(attachment_id)]
    if len(choices) != 1:
        raise ValueError('附件不在官方目录')
    r = _get(choices[0]['url'], 30)
    if not r.content.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise RuntimeError('响应不是 XLS 文件')
    return (choices[0], xlrd.open_workbook(file_contents=r.content))

def sheets(attachment_id):
    source, book = _workbook(attachment_id)
    return {'source': source, 'sheets': [{'name': s.name, 'rows': s.nrows, 'columns': s.ncols} for s in book.sheets()]}

def rows(attachment_id, sheet, offset=0, limit=100):
    if int(offset) < 0 or not 1 <= int(limit) <= 500:
        raise ValueError('offset 非负，limit 为 1–500')
    source, book = _workbook(attachment_id)
    if sheet not in book.sheet_names():
        raise ValueError('工作表不存在')
    s = book.sheet_by_name(sheet)
    start = int(offset)
    end = min(s.nrows, start + int(limit))
    return {'source': source, 'sheet': sheet, 'total_rows': s.nrows, 'offset': start, 'rows': [[s.cell_value(i, j) for j in range(s.ncols)] for i in range(start, end)], 'note': '原始单元格值，不传播合并单元格，空值不视为零。'}
