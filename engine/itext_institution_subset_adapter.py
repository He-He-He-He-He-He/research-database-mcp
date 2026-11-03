"""爱教材浙大 IP 的 Wiley/CRC 子库首页书目。"""
import release_runtime
import re
from urllib.parse import urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup
URL = 'https://www.itextbook.cn/f/db/officeDbDetail'
PRODUCTS = {'wiley': 'f0c99a89ee5f4852b4c996a65eefa88e', 'crc': '75fcf6f226454e898939e13a58b77d63'}

def browse(product, limit=10, session=None):
    if product not in PRODUCTS:
        raise ValueError('子库须为 wiley 或 crc')
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('limit 须为 1–10')
    s = session or requests.Session()
    try:
        r = s.get(URL, params={'connDbId': PRODUCTS[product]}, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('子库页面不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        text = p.get_text(' ', strip=True)
        if not re.search('浙江大学\\s*IP\\s*(?:Reader|读者)', text, re.I):
            raise RuntimeError('未确认浙江大学 IP 读者身份')
        if not any((x.get('name') == 'connDbId' and x.get('value') == PRODUCTS[product] for x in p.select('input[name]'))):
            raise RuntimeError('页面未确认所选子库')
        nav = p.select_one('div.page')
        count = re.search('(?:total\\s*:|总计[：:])\\s*([\\d,]+)', nav.get_text(' ', strip=True), re.I) if nav else None
        if not count:
            raise RuntimeError('无法识别站方总数')
        cards = p.select('.book-info')
        total = int(count.group(1).replace(',', ''))
        if total < 0 or len(cards) != min(10, total):
            raise RuntimeError('首页数量与站方总数不一致')
        items = []
        for x in cards[:limit]:
            a = x.select_one('p.title a')
            u = urlsplit(a.get('href', '')) if a else None
            if not a or u.path != '/f/book/bookDetail' or u.netloc not in ('', 'www.itextbook.cn'):
                raise RuntimeError('书目链接格式异常')
            q = parse_qs(u.query)
            ids = q.get('bookId', [])
            if len(ids) != 1 or not re.fullmatch('[A-Za-z0-9]{32}', ids[0]):
                raise RuntimeError('书目编号格式异常')
            title = a.get_text(' ', strip=True)
            author = x.select_one('.start-group')
            extra = x.select('p.text')
            if not title:
                raise RuntimeError('书名缺失')
            items.append({'book_id': ids[0], 'title': title, 'author_raw': author.get_text(' ', strip=True) if author else None, 'other_lines_raw': [v.get_text(' ', strip=True) for v in extra]})
        return {'source': '爱教材子库首页', 'institution': '浙江大学 IP Reader', 'product': product, 'total_raw': total, 'items': items, 'page_truncated': len(items) < min(10, total), 'has_more_pages': total > 10, 'note': '仅当前子库首页，网页总数为站方显示值，非完整名单或逐本订购/全文权利证明；不输出页面会话链接。'}
    except requests.RequestException:
        raise RuntimeError('爱教材服务连接失败') from None
