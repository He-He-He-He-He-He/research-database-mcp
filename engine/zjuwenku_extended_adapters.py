"""浙大文库统一检索分页、书目详情；不获取全文。"""
import release_runtime
import argparse, json, re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE, Parser
from zjuwenku_page_counts import validate_page_count

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为1–1000')
    p = {'keyword': keyword.strip(), 'sall': '0', 'pageSize': '10', 'pageNumber': str(page), 'category': '0', 'type': '0'}
    with urlopen(BASE + 'search?' + urlencode(p), timeout=20) as r:
        html = r.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    pager = soup.select_one('.m-page')
    if not pager:
        parser = Parser()
        parser.feed(html)
        if page == 1 and soup.title and (soup.title.get_text(' ', strip=True) == '浙大文库 - 统一搜索 - 搜索结果') and ('没有相关结果' in soup.get_text(' ', strip=True)) and (not parser.items):
            return {'source': '浙大文库', 'query': keyword.strip(), 'page': 1, 'pages': 0, 'total': 0, 'items': [], 'note': '原站明确显示没有相关结果；网页使用明文 HTTP，勿传敏感关键词。'}
        raise RuntimeError('未识别分页，可能无结果或网站变更')
    text = pager.get_text(' ', strip=True)
    pg = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页', text)
    tot = re.search('共\\s*(\\d+)\\s*条记录', text)
    if not pg or not tot or int(pg.group(1)) != page:
        raise RuntimeError('未确认所请求页码')
    parser = Parser()
    parser.feed(html)
    pages = int(pg.group(2))
    total = int(tot.group(1))
    validate_page_count(total, pages, page, parser.items, 10)
    if any((not x.get('text') or not x.get('url') for x in parser.items)):
        raise RuntimeError('统一检索题录字段缺失')
    return {'source': '浙大文库', 'query': keyword.strip(), 'page': page, 'pages': pages, 'total': total, 'items': parser.items, 'note': '统一搜索包括书目作品、人物及动态，单页；网页使用明文 HTTP，勿传敏感关键词。'}

def book_detail(book_id):
    if not isinstance(book_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', book_id):
        raise ValueError('图书编号须为32位十六进制')
    book_id = book_id.lower()
    url = BASE + 'search/book/detail?' + urlencode({'id': book_id})
    with urlopen(url, timeout=20) as r:
        html = r.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one('table.m-table-c2')
    if not table:
        raise RuntimeError('未识别书目表')
    fields = []
    for cell in table.select('th,td'):
        t = cell.get_text(' ', strip=True)
        k, sep, v = t.partition('：')
        if sep and k:
            fields.append({'label': k, 'value': v})
    if not any((f['label'] == '题名' and f['value'] for f in fields)):
        raise RuntimeError('书目无题名，页面结构或权限可能发生变化')
    return {'source': '浙大文库书目详情', 'record_url': url, 'fields': fields, 'note': '只读取书目基本字段，未获取内容简介、图片或全文；其他类型详情不支持。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('search')
    x.add_argument('keyword')
    x.add_argument('--page', type=int, default=1)
    x = sub.add_parser('book')
    x.add_argument('id')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page) if a.cmd == 'search' else book_detail(a.id), ensure_ascii=False, indent=2))
