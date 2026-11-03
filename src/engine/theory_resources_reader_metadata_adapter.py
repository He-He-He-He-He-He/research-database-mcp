"""思想理论资源库阅读器初始化中的图书元数据；不读取正文或图片。"""
import release_runtime
import json
import re
import requests
from bs4 import BeautifulSoup
from theory_resources_ip_catalog_adapter import BASE

def metadata(book_id, expected_title):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', book_id):
        raise ValueError('书号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200:
        raise ValueError('须提供完整书名')
    p = {'logic': 'PDFReaderController', 'call': 'readPDF', 'page': '1', 'bookid': book_id, 'html': 'selectText_NOINC', 'from': 'online', 'searchChar': ''}
    r = requests.get(BASE + 'Service/', params=p, timeout=25)
    r.raise_for_status()
    page = BeautifulSoup(r.content, 'html.parser')
    if not page.title or page.title.get_text(' ', strip=True) != '在线阅读':
        raise RuntimeError('未进入原站阅读器')
    match = re.search('var\\s+initData\\s*=\\s*(\\{.*?\\});\\s*</script>', r.text, re.S)
    if not match:
        raise RuntimeError('原站初始化元数据缺失')
    try:
        data = json.loads(match.group(1))
    except ValueError:
        raise RuntimeError('原站元数据格式异常') from None
    books = data.get('bookinfo') if isinstance(data, dict) else None
    if data.get('readPDFErr') or data.get('currentPage') != 1 or (not isinstance(books, list)) or (len(books) != 1) or (not isinstance(books[0], dict)):
        raise RuntimeError('原站未提供有效阅读器信息')
    book = books[0]
    if book.get('bookid') != book_id or book.get('bookname') != expected_title.strip() or type(book.get('pages')) is not int or (book['pages'] < 1):
        raise RuntimeError('书目编号、标题或阅读器页数不一致')
    return {'source': '中国共产党思想理论资源数据库及扩展库', 'institution': '未单独标识', 'book_id': book_id, 'book': book, 'note': '校内 HTTP 阅读器返回的单册原始元数据和页数，日期可能是时间戳；仅表明页面初始化可见，不代表正文或全文权限。'}
