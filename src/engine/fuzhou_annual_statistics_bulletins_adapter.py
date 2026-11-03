"""Official Fuzhou annual economic and social statistical bulletins."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
INDEX = 'https://tjj.fuzhou.gov.cn/zwgk/tjzl/ndbg/'

def _get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def catalog():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.fullmatch('(\\d{4})年福州市国民经济和社会发展统计公报', title)
        url = urljoin(INDEX, a['href'])
        if m and urlparse(url).scheme == 'https' and (urlparse(url).netloc == 'tjj.fuzhou.gov.cn') and (url not in seen):
            items.append({'year': int(m.group(1)), 'title': title, 'url': url})
            seen.add(url)
    if not items:
        raise ValueError('official directory format changed')
    return items

def bulletin(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year must be integer')
    matches = [x for x in catalog() if x['year'] == year]
    if len(matches) != 1:
        raise ValueError('year missing or ambiguous')
    item = matches[0]
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    body = soup.select_one('.TRS_Editor')
    if not body:
        raise ValueError('article body missing')
    tables = []
    for table in body.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    images = [urljoin(item['url'], i['src']) for i in body.find_all('img', src=True)]
    text = body.get_text('\n', strip=True)
    if not text and (not images):
        raise ValueError('article has no text or images')
    return {'source': '福州市统计局', 'year': year, 'source_url': item['url'], 'text': text, 'tables': tables, 'image_urls': images}
