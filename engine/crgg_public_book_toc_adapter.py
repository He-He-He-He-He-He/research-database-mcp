"""国别区域与全球治理平台匿名公开图书目录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.crggcn.com/skwx_crgg/'

def book_toc(content_id, expected_title):
    content_id = str(content_id)
    if not re.fullmatch('[0-9]{1,16}', content_id):
        raise ValueError('content_id 须为数字')
    if not isinstance(expected_title, str) or not 1 <= len(expected_title.strip()) <= 300 or any((ord(c) < 32 for c in expected_title)):
        raise ValueError('须提供检索结果原始题名')
    with requests.Session() as session:
        r = session.get(BASE + 'bookdetail', params={'SiteID': '25', 'ID': content_id}, timeout=25)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        if not p.title or p.title.get_text(' ', strip=True) != expected_title.strip() + '_区域国别与全球治理数据库':
            raise RuntimeError('图书页标题与预期不符')
        if not re.search('bookdetail/dir\\?ID=' + re.escape(content_id) + '[^0-9]', r.text):
            raise RuntimeError('图书目录请求编号未确认')
        r = session.get(BASE + 'bookdetail/dir', params={'ID': content_id}, timeout=25)
        r.raise_for_status()
        try:
            rows = r.json()
        except ValueError:
            raise RuntimeError('目录未返回 JSON') from None
    if not isinstance(rows, list):
        raise RuntimeError('目录结构异常')
    count = 0

    def convert(nodes, depth):
        nonlocal count
        if not isinstance(nodes, list) or depth > 20:
            raise RuntimeError('目录层级异常')
        out = []
        for x in nodes:
            count += 1
            if count > 10000 or not isinstance(x, dict) or type(x.get('id')) is not int or (not isinstance(x.get('searchTitle'), str)):
                raise RuntimeError('目录节点异常')
            children = convert(x.get('children', []), depth + 1)
            out.append({'id': x['id'], 'title': x['searchTitle'], 'innercode_raw': x.get('innercode'), 'minnodesearch_raw': x.get('minnodesearch'), 'children': children})
        return out
    toc = convert(rows, 1)
    return {'source': '国别区域与全球治理平台公开图书目录', 'content_id': content_id, 'title': expected_title.strip(), 'node_count': count, 'items': toc, 'note': '匿名公开图书页核对题名和目录编号；仅返回站方目录及原始标记，空目录不代表空书；未读取正文，学校身份及全文权限未验证。'}
