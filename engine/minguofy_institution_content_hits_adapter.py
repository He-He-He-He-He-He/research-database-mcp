"""书同文民国风云全文命中结果页短片段。"""
import release_runtime
import re, requests
from bs4 import BeautifulSoup
BASE = 'https://gujiku.unihan.com.cn/'

def search(keyword, offset=0, limit=10):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or any((ord(c) < 32 or c == '+' for c in keyword)):
        raise ValueError('关键词须为1–100字单行文本且不含加号')
    if type(offset) is not int or not 0 <= offset <= 100000 or type(limit) is not int or (not 1 <= limit <= 30):
        raise ValueError('offset 或 limit 无效')
    q = keyword.strip()
    try:
        with requests.Session() as s:
            r = s.get(BASE + 'Products/Search/QSL', timeout=20)
            r.raise_for_status()
            if not re.search('\\bzjdx\\b', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True), re.I):
                raise RuntimeError('未确认书同文学校账户标记')
            r = s.get(BASE + 'minguofy/api/oldsearch/MinGuoSearchContent', params={'word': q, 'start': offset, 'count': limit}, timeout=20)
            r.raise_for_status()
            d = r.json()
    except requests.RequestException:
        raise RuntimeError('书同文请求失败') from None
    if not isinstance(d, dict) or d.get('searchStr') != q or d.get('start') != offset or (type(d.get('total')) is not int) or (d['total'] < 0) or (type(d.get('count')) is not int) or (not isinstance(d.get('items'), list)) or (d['count'] != len(d['items'])) or (len(d['items']) > limit):
        raise RuntimeError('文献检索条件或分页异常')
    items = []
    for x in d['items']:
        if not isinstance(x, dict) or any((not isinstance(x.get(k), str) for k in ('title', 'categories', 'content'))):
            raise RuntimeError('文献字段异常')
        if any((re.search('(?i)(?:https?://|(?:token|session|sid|apikey)\\s*=)', x[k]) for k in ('title', 'categories', 'content'))):
            raise RuntimeError('文献字段包含异常链接或凭据')
        content = x['content']
        items.append({'title_raw': x['title'], 'categories_raw': x['categories'], 'snippet_raw_html': content[:1000], 'snippet_locally_truncated': len(content) > 1000})
    return {'source': '书同文民国风云文献命中片段', 'account_marker': 'zjdx（书同文账户）', 'query': q, 'offset': offset, 'limit': limit, 'total': d['total'], 'items': items, 'note': '站方回显检索词与起始位置；仅结果页片段，保留高亮 HTML，可能截断，不等于完整正文。书同文账户标记不证明此产品单独授权；不返回底层文件、偏移或会话链接。'}
