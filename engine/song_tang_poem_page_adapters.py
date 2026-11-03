"""Published trial catalogs for Tang/Song poetry: normal results-page navigation."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'http://www.chinabooktrading.com/'

def page(kind, keyword, page=2, session=None):
    if kind not in ('song', 'tang') or not isinstance(keyword, str) or (not keyword.strip()) or (len(keyword) > 100) or (type(page) is not int) or (not 2 <= page <= 1000):
        raise ValueError('需要 song/tang、关键词和 2–1000 页')
    query = keyword.strip()
    p = {'e': '1' if kind == 'song' else '0', 'a': '1', 'j': '0', 'b': '1', 'm': query, 'c': str(page)}
    r = (session or requests).get(BASE + kind + '/resultList.jsp', params=p, timeout=20)
    r.raise_for_status()
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text(' ', strip=True)
    label = '宋詩' if kind == 'song' else '唐詩'
    if f'檢索條件為：{label}' not in text or f'詩内容含有關鍵字：{query}' not in text:
        raise ValueError('页面诗集或检索条件不匹配')
    m = re.search('共\\s*(\\d+)\\s*條信息，當前顯示\\s*(\\d+)\\s*至\\s*(\\d+)\\s*條', text)
    n = re.search('共\\s*(\\d+)\\s*頁\\s*,\\s*當前第\\s*(\\d+)\\s*頁', text)
    if not m or not n or int(n.group(2)) != page:
        raise ValueError('页码或结果总数无法确认')
    items = [{'title': a.get_text(' ', strip=True), 'url': urljoin(BASE + kind + '/', a.get('href'))} for a in soup.select('a[href^="fullText.jsp?"]') if a.get_text(' ', strip=True)]
    if len(items) != int(m.group(3)) - int(m.group(2)) + 1:
        raise ValueError('实际题录数与页面范围不一致')
    return {'source': '全宋诗分析系统' if kind == 'song' else '全唐诗分析系统', 'scope': '公开试用版本，仅含部分诗', 'query': query, 'page': page, 'page_count': int(n.group(1)), 'total': int(m.group(1)), 'items': items, 'note': '原站诗内容关键词检索的当前页题名；HTTP 明文传输，请勿输入敏感信息。未验证全文权限。'}
