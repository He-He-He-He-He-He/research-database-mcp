"""MOT urban rail operation bulletin catalog and article paragraphs."""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.mot.gov.cn/shuju/fenxigongbao/yunlifenxi/'

def catalog(page=0, keyword=''):
    if not isinstance(page, int) or not 0 <= page <= 4:
        raise ValueError('page must be 0–4')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    u = BASE + ('index.html' if page == 0 else f'index_{page}.html')
    r = requests.get(u, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        url = urljoin(u, a['href'])
        if '城市轨道交通运营数据速报' not in title or keyword not in title or (not url.startswith(BASE)) or (not url.endswith('.html')):
            continue
        if url not in seen:
            items.append({'title': title, 'url': url})
            seen.add(url)
    return {'source': '中华人民共和国交通运输部', 'source_url': u, 'items': items}

def bulletin(url):
    matched = None
    for page in range(5):
        matched = next((x for x in catalog(page)['items'] if x['url'] == url), None)
        if matched:
            break
    if matched is None:
        raise ValueError('URL is not in catalog pages 0–4')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('#article-content')
    if not body:
        raise ValueError('article body missing')
    paragraphs = [p.get_text('', strip=True) for p in body.find_all('p') if p.get_text('', strip=True)]
    if not paragraphs:
        raise ValueError('article paragraphs missing')
    return {'source': '中华人民共和国交通运输部', **matched, 'paragraphs': paragraphs}
