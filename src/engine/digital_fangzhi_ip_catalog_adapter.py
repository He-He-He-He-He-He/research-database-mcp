"""Campus Chinese Digital Gazetteer catalog, no full text."""
import release_runtime
import re
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
BASE = 'http://10.15.61.5/'
ID_RE = re.compile('BookDetails\\.aspx\\?pID=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:&|$)', re.I)

def _plain(v):
    return BeautifulSoup(v or '', 'html.parser').get_text(' ', strip=True)

def search(keyword, page=1, limit=15, session=None, field='all'):
    modes = {'all': '2', 'title': '3', 'author': '4', 'text': '14'}
    if field not in modes:
        raise ValueError('不支持的检索字段')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 12:
        raise ValueError('关键词须为 1–12 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 15):
        raise ValueError('每页最多 15 条')
    q = keyword.strip()
    s = session or requests.Session()
    home = s.get(BASE, timeout=20)
    home.raise_for_status()
    if '欢迎您：浙江大学' not in BeautifulSoup(home.content, 'html.parser').get_text(' ', strip=True):
        raise RuntimeError('未确认浙江大学机构身份')
    r = s.post(BASE + 'bookListHandler.ashx', data={'action': 'getpagedata', 'pagenum': str(page), 'pSet': modes[field], 'SearchKeyword': q}, timeout=20)
    r.raise_for_status()
    rows = r.json()
    if not isinstance(rows, list) or len(rows) > 15:
        raise RuntimeError('异常检索响应')
    items = []
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError('异常题录')
        if field == 'text':
            a = BeautifulSoup(row.get('TextReading') or '', 'html.parser').find('a')
            m = re.match("\\s*Book_Read\\(\\s*'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'\\s*,\\s*'([^']+)'", a.get('onclick', ''), re.I) if a else None
            if not m:
                raise RuntimeError('阅读器书号或题名缺失')
            ident, title = (m.group(1), m.group(2).strip())
            if not title or re.sub('\\s+', '', title) not in re.sub('\\s+', '', _plain(row.get('Title_Liability'))):
                raise RuntimeError('阅读器题名与题录不符')
            item = {'id': ident, 'id_type': 'reader_book_id', 'title': title, 'section': _plain(row.get('ContenTtitle')), 'edition': _plain(row.get('pVersion')) or None, 'publication_year': _plain(row.get('pPublicationYear')) or None, 'url': None}
        else:
            a = BeautifulSoup(row.get('Title_Liability') or '', 'html.parser').find('a', href=True)
            m = ID_RE.match(a['href']) if a else None
            if not m:
                raise RuntimeError('题录编号缺失')
            ident = m.group(1)
            title = a.get_text(' ', strip=True)
            item = {'id': ident, 'title': title, 'section': _plain(row.get('ContenTtitle')), 'edition': _plain(row.get('pVersion')) or None, 'publication_year': _plain(row.get('pPublicationYear')) or None, 'url': BASE + 'BookDetails.aspx?' + urlencode({'pID': ident})}
        if field == 'author':
            item['title_responsibility_raw'] = _plain(row.get('Title_Liability'))
        items.append(item)
    result = {'source': '中国数字方志库', 'institution': '浙江大学', 'query': q, 'page': page, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '校园内网 HTTP；每页原站最多 15 条，同一本书可能按章节重复；空页不区分无结果和页码超范围，未验证全文权限；limit只截取原站当前页，若truncated为true，翻到下一站方页会遗漏本页其余结果，请用limit=15取整页。'}
    if field == 'author':
        result['note'] += ' title_responsibility_raw 是去标签、整理空白后的来源显示文字，并非原始 HTML。'
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 按官网字段请求，站方未回显字段或页码；正文关键词检索只返回题录，不证明正文权限。'
    return result
