"""SMF public publications catalogue, one fixed-size source page."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
URL = 'https://smf.emath.fr/les-publications'

def search(keyword, page=1, timeout=25):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((x in keyword for x in '\r\n')):
        raise ValueError('关键词须为1至100字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('页码须为1至10000')
    keyword = keyword.strip()
    try:
        r = requests.get(URL, params={'search': keyword, 'page': page - 1}, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException:
        raise RuntimeError('SMF目录请求失败') from None
    if urlsplit(r.url).hostname != 'smf.emath.fr':
        raise RuntimeError('SMF目录转到了非预期网站')
    s = BeautifulSoup(r.text, 'html.parser')
    q = s.select_one('input[name="search"]')
    count = s.select_one('.view__results_count')
    if not q or q.get('value') != keyword or (not count):
        raise RuntimeError('无法核对站方检索词或结果计数')
    m = re.match('^\\s*([0-9\\s\\u00a0\\u202f]+)\\s+publications?\\b', count.get_text(' ', strip=True), re.I)
    if not m:
        raise RuntimeError('无法解析站方结果计数')
    total = int(re.sub('\\s', '', m.group(1)))
    cards = s.select('a.publication')
    expected = min(12, max(0, total - (page - 1) * 12))
    if len(cards) != expected:
        raise RuntimeError('结果条数与站方总数或请求页不符')
    items = []
    for card in cards:

        def value(css):
            node = card.select_one(css)
            return node.get_text(' ', strip=True) if node else None
        title = value('.publication__title')
        if not title:
            raise RuntimeError('结果标题缺失')
        u = urlsplit(urljoin(URL, card.get('href', '')))
        safe_url = u.geturl() if u.scheme == 'https' and u.hostname == 'smf.emath.fr' and u.path.startswith('/publications/') and (not u.query) and (not u.fragment) and (not u.username) and (not u.password) else None
        items.append({'title': title, 'authors': value('.publication__text'), 'collection': value('.publication__collection'), 'citation_raw': value('.publication__more_info'), 'url': safe_url})
    return {'source': 'Société Mathématique de France 公开出版物目录', 'keyword': keyword, 'page': page, 'page_size': 12, 'total': total, 'items': items, 'note': '原站目录含文章和图书；搜索可能匹配其他字段，页面未回显当前页码，排序和总数可能变化。匿名访问，未验证浙大机构身份、订购范围及全文权限。'}
