"""漢達文庫校园 IP 快速检索：仅读取少量书目位置。"""
import release_runtime
import re
from urllib.parse import quote, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.chant.org'

def search(keyword, limit=5, *, offset=0):
    if not isinstance(keyword, str) or not 1 <= len(keyword) <= 30 or (not keyword.isalnum()):
        raise ValueError('关键词须为1–30个文字或数字，不含空白')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为1–10')
    with requests.Session() as session:
        r = session.get(BASE + '/search/FastSearch', timeout=25)
        r.raise_for_status()
        if '[Zhejiang University]' not in BeautifulSoup(r.text, 'html.parser').get_text(' ', strip=True):
            raise RuntimeError('未识别浙大机构会话')
        r = session.get(BASE + '/result/FastSearch/' + quote(keyword, safe=''), params={'SearchConfig': 'All', 'Target': keyword, 'SearchGroup': 'Book'}, timeout=30)
        r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text(' ', strip=True)
    heading = soup.find('h3')
    if '[Zhejiang University]' not in text or not heading or heading.get_text(' ', strip=True) != '【' + keyword + '】':
        raise RuntimeError('结果关键词或浙大机构身份不符')
    hits = re.search('結果總數：\\s*([\\d,]+)', text)
    books = re.search('共\\s*([\\d,]+)\\s*書目', text)
    if not hits or not books:
        raise RuntimeError('未识别命中数或书目数；零结果尚未验证')
    items = []
    source_rows = soup.find_all('h5')
    for h in source_rows[offset:offset + limit]:
        links = []
        for a in h.select('a[href]')[:2]:
            u = urlsplit(a['href'])
            if u.scheme != 'https' or u.hostname != 'www.chant.org' or (not u.path.startswith('/text/book/')):
                raise RuntimeError('书目链接不符合原站范围')
            links.append({'title': a.get_text(' ', strip=True), 'url': a['href']})
        if not links:
            raise RuntimeError('结果缺少书目链接')
        items.append({'location': h.get_text(' ', strip=True), 'links': links})
    if not source_rows and int(hits.group(1).replace(',', '')):
        raise RuntimeError('结果书目位置未识别')
    return {'source': '漢達文庫校园 IP 快速检索', 'institution': 'Zhejiang University', 'query': keyword, 'search_config': 'All', 'search_group': 'Book', 'matched_hits': int(hits.group(1).replace(',', '')), 'matched_books': int(books.group(1).replace(',', '')), 'source_locations': len(source_rows), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(source_rows) else None, 'items': items, 'note': '请求 SearchGroup=Book、SearchConfig=All；源站未回显分组，2026-11-02 将 Bone 与 Book 分组分别查询春秋、甲子均得到相同计数和首条，分组筛选是否生效未确认，不能据此推断仅限传世或包含甲骨。结果位置数与书目数不同，不可混同；每次重新获取来源结果页并本地截取书目位置，来源排序可能变化；只输出少量书目位置，不输出正文或图片；校园会话可能变化。'}
