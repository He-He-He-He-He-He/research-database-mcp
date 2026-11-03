"""Hunan official annual economic and social statistical bulletins."""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin
from bs4 import BeautifulSoup
INDEX = 'https://tjj.hunan.gov.cn/tjfx/tjgb/jjfzgb/'

def _get(url):
    return release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', url], capture_output=True, check=True, timeout=35).stdout

def catalog():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        match = re.fullmatch('湖南省(\\d{4})年国民经济和社会发展统计公报', title)
        url = urljoin(INDEX, a['href'])
        if match and url.startswith('https://tjj.hunan.gov.cn/'):
            items.append({'year': int(match.group(1)), 'title': title, 'url': url})
    if not items:
        raise ValueError('bulletin catalog format changed')
    return items

def bulletin(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year must be an integer')
    matches = [x for x in catalog() if x['year'] == year]
    if len(matches) != 1:
        raise ValueError('year missing or ambiguous in catalog')
    item = matches[0]
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    body = soup.select_one('#d_article')
    if not body or not body.get_text(strip=True):
        raise ValueError('bulletin body missing')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return {'source': '湖南省统计局', 'year': year, 'source_url': item['url'], 'text': body.get_text('\n', strip=True), 'tables': tables, 'image_urls': [urljoin(item['url'], i['src']) for i in body.find_all('img', src=True)]}
