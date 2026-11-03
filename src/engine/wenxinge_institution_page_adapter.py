"""文心阁校园 IP 阅读器单页原文，不保存会话标识或下载图像。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from wenxinge_institution_catalog_adapter import BASE

def page(book_id, reader_title, page=1):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{32}', book_id):
        raise ValueError('图书编号无效')
    if not isinstance(reader_title, str) or not reader_title.strip() or len(reader_title) > 200:
        raise ValueError('须提供阅读器显示的书名')
    if type(page) is not int or not 1 <= page <= 100000:
        raise ValueError('页码须为正整数')
    with requests.Session() as s:
        r = s.get(BASE + 'home/doc/index.do', timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        if '浙江大学' not in p.get_text(' ', strip=True):
            raise RuntimeError('未确认浙江大学机构身份')
        flag = p.select_one('#ytzFlag')
        if not flag or not flag.get('value'):
            raise RuntimeError('缺少阅读器参数')
        path = 'home/readPage/' + book_id + '/' + str(page) + '/'
        r = s.get(BASE + path + 'index.do', params={'ytzFlag': flag['value']}, timeout=25)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')

        def value(k):
            node = p.select_one('#' + k)
            return node.get('value') if node else None
        total = value('pageCount')
        client = value('clientUuid')
        if value('documentGuid') != book_id or value('initPageNum') != str(page) or value('documentName') != reader_title.strip() or (not total) or (not total.isdigit()) or (not client) or (not re.fullmatch('[A-Za-z0-9-]{1,100}', client)):
            raise RuntimeError('阅读器书号、标题或页码不匹配')
        if page > int(total):
            raise ValueError('页码超过站方总页数')
        r = s.get(BASE + path + 'tra/showHtml.do', params={'clientUuid': client}, timeout=25)
        r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    docs = p.select('.document')
    if len(docs) != 1 or not docs[0].get_text('', strip=True):
        raise RuntimeError('站方未返回页面原文')
    return {'source': '文心阁古籍数据库', 'institution': '浙江大学', 'book_id': book_id, 'reader_title': reader_title.strip(), 'page': page, 'reader_page_count': int(total), 'page_html': str(docs[0]), 'note': '站方繁体原文及注释排版 HTML；阅读器显示书名可能与检索书名异体字不同。正文响应未回显书号和页码，已在同一会话核对阅读器上下文；单页可读不保证其他书页权限。'}
