"""Science Reading institution book table of contents; no book pages."""
import release_runtime
import json
import re
import requests
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
BASE = 'https://book.sciencereading.cn/'

def contents(book_id, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{1,100}', book_id):
        raise ValueError('图书编号无效')
    s = session or requests.Session()
    r = s.get(BASE + 'shop/main/Login/shopFrame.do', timeout=25)
    r.raise_for_status()
    r = s.post(BASE + 'shop/main/Login/checkOrgNameByIp.do', timeout=20)
    r.raise_for_status()
    if r.text.strip() != '浙江大学':
        raise RuntimeError('未确认浙江大学 IP 机构身份')
    r = s.get(BASE + 'shop/book/Booksimple/show.do', params={'id': book_id}, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    bid = p.select_one('input#id')
    title = p.title.get_text('', strip=True) if p.title else ''
    if not bid or bid.get('value') != book_id or (not title):
        raise RuntimeError('图书身份未确认')
    m = re.search('var\\s+zNodes\\s*=\\s*(\\[.*?\\]);', r.text, re.S)
    if not m:
        raise RuntimeError('未识别图书目录')
    try:
        nodes = json.loads(m.group(1))
    except ValueError as e:
        raise RuntimeError('目录格式异常') from e
    if not isinstance(nodes, list) or len(nodes) > 10000:
        raise RuntimeError('目录数量异常')
    out = []
    for x in nodes:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('name'), str)):
            raise RuntimeError('目录字段缺失')
        entry = {'id': x['id'], 'parent_id': x.get('pId'), 'name': x['name']}
        url = x.get('url')
        if isinstance(url, str):
            parsed = urlsplit(url)
            q = parse_qs(parsed.query)
            if not parsed.netloc and parsed.path == '/shop/book/Booksimple/onlineRead.do' and (q.get('id') == [book_id]) and (len(q.get('bookPageNum', [])) == 1) and re.fullmatch('[0-9]{1,8}', q['bookPageNum'][0]):
                entry['reader_page_number'] = int(q['bookPageNum'][0])
        out.append(entry)
    return {'source': '科学文库', 'institution': '浙江大学', 'book_id': book_id, 'title': title, 'entries': out, 'note': '原站书籍目录节点及层级；reader_page_number 为阅读器页面编号，未必等于印刷页码；未验证逐书全文权限。'}
