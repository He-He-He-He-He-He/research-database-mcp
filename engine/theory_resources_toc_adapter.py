"""校内思想理论资源及扩展库的图书目录，不读取正文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from theory_resources_ip_catalog_adapter import BASE

def contents(book_id, expected_title):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', book_id):
        raise ValueError('图书编号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200:
        raise ValueError('须提供完整书名')
    r = requests.get(BASE + 'Service/', params={'logic': 'bookController', 'call': 'getContentByBook', 'bookid': book_id}, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if not p.title or '目录详情' not in p.title.get_text(' ', strip=True):
        raise RuntimeError('未进入图书目录')
    rows = []
    for li in p.select('li[beginpage]'):
        a = li.find('a', recursive=False)
        page = li.get('beginpage', '')
        if not a or not page.isdigit() or (not re.fullmatch("javascript:\\s*readBook\\('" + re.escape(book_id) + "',\\s*" + re.escape(page) + '\\)', a.get('href', '').strip())):
            raise RuntimeError('目录编号或页码不一致')
        rows.append({'title_raw': a.get_text(' ', strip=True), 'reader_page_number': int(page), 'depth': len(li.find_parents('li'))})
    if not rows or rows[0]['title_raw'].replace('\x00', '').strip() != expected_title.strip():
        raise RuntimeError('图书标题不一致')
    return {'source': '中国共产党思想理论资源数据库及扩展库', 'institution': '未单独标识', 'book_id': book_id, 'title': expected_title, 'entries': rows, 'note': '校园内网 HTTP 图书目录，原站部分目录含空字符，原样保留；页码为阅读器页序，未必为印刷页码，未读取正文或验证全文权限。'}
