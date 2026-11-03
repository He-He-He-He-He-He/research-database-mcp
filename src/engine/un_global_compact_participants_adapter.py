"""UN Global Compact public participant directory website search."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://unglobalcompact.org'
URL = BASE + '/what-is-gc/participants/search'

def _parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one('table.participants-table')
    count = soup.select_one('.results-count')
    if table is None:
        section = soup.select_one('section.main-content-section')
        if section and section.get_text(' ', strip=True) == 'No results.':
            return (0, [])
        raise ValueError('unexpected directory page')
    if count is None:
        raise ValueError('result count missing')
    matches = re.findall('([\\d,]+)\\s+results?\\b', count.get_text(' ', strip=True), re.I)
    if not matches:
        raise ValueError('cannot parse result count')
    rows = []
    for tr in table.select('tbody tr'):
        a = tr.select_one('th.name a')
        cells = tr.find_all('td', recursive=False)
        if not a or len(cells) != 4:
            raise ValueError('unexpected participant row')
        rows.append({'name': a.get_text(' ', strip=True), 'url': urljoin(BASE, a.get('href', '')), 'type': cells[0].get_text(' ', strip=True), 'sector': cells[1].get_text(' ', strip=True), 'country': cells[2].get_text(' ', strip=True), 'joined_on': cells[3].get_text(' ', strip=True)})
    return (int(matches[-1].replace(',', '')), rows)

def search(keyword, page=1, per_page=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('invalid keyword')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or (per_page not in (10, 25, 50)) or isinstance(per_page, bool):
        raise ValueError('invalid pagination')
    p = {'search[keywords]': keyword, 'search[per_page]': per_page, 'page': page}
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    total, rows = _parse(r.text)
    return {'source': r.url, 'directory': BASE + '/what-is-gc/participants', 'total': total, 'page': page, 'per_page': per_page, 'rows': rows, 'note': 'Public UN Global Compact participant directory: participation is a voluntary commitment, not certification, endorsement or independent proof of ESG performance. Search results depend on source matching and may change. Joined date does not establish current reporting or member status; inspect each participant profile. Website parsing may change.'}
