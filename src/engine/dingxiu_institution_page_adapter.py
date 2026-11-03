"""鼎秀古籍机构会话单页原文，保留原站版式与注释 HTML。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from dingxiu_institution_catalog_adapter import BASE
READER = 'https://www.ding-xiu.com/ancientbook/portal/readPage/'

def page(guid, expected_title, page=1):
    if not isinstance(guid, str) or not re.fullmatch('[A-Za-z0-9]{32}', guid):
        raise ValueError('图书 GUID 无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200:
        raise ValueError('须提供原站繁体书名')
    if type(page) is not int or not 1 <= page <= 100000:
        raise ValueError('页码须为正整数')
    with requests.Session() as s:
        r = s.get(BASE + 'index.do', timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        inst = p.select_one('#nologin')
        if not inst or not re.search('机构\\s*[:：]\\s*浙江大学', inst.get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(READER + guid + '/' + str(page) + '/index.do', timeout=25)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        b = p.select_one('#documentGuid')
        num = p.select_one('#initPageNum')
        total = p.select_one('#pageCount')
        title = p.select_one('.conttitleleft')
        if not b or b.get('value', '').lower() != guid.lower() or (not num) or (num.get('value') != str(page)) or (not total) or (not total.get('value', '').isdigit()) or (not title) or (title.get_text(' ', strip=True) != expected_title.strip()):
            raise RuntimeError('阅读器书号、标题或页码不匹配')
        page_count = int(total['value'])
        if page > page_count:
            raise ValueError('页码超过站方总页数')
        r = s.get(READER + guid + '/' + str(page) + '/tra/showHtml.do', timeout=25)
        r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    nodes = p.select('.document')
    if len(nodes) != 1 or not nodes[0].get_text('', strip=True):
        raise RuntimeError('站方未返回页面原文')
    return {'source': '鼎秀古籍全文检索平台', 'institution': '浙江大学', 'guid': guid, 'title': expected_title.strip(), 'page': page, 'reader_page_count': page_count, 'page_html': str(nodes[0]), 'note': '站方繁体版式原始 HTML，含原文与小字注释；阅读器页数不一定等于印刷页。正文响应不回显书号及页码，已核验阅读器请求上下文；当前单页可读不代表其他图书权限。'}
