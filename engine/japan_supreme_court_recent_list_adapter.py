"""Japan Courts official recently published Supreme Court judgments list."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
URL = 'https://www.courts.go.jp/hanrei/search2/index.html'

def recent(limit=10):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    r = requests.get(URL, params={'courtCaseType': '1', 'filter[recent]': '1'}, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Unexpected response size')
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.select_one('table.search-result-table')
    if not table:
        raise ValueError('Results table not found; no inference of zero')
    rows = []
    for tr in table.select('tr'):
        a = tr.select_one('a[href*="/detail2/"]')
        cells = tr.select('td')
        if not a or not cells:
            continue
        detail = urljoin(URL, a.get('href', ''))
        if urlparse(detail).hostname != 'www.courts.go.jp' or not re.fullmatch('/hanrei/[0-9]+/detail2/index.html', urlparse(detail).path):
            raise ValueError('Unexpected detail URL')
        pdf = tr.select_one('a[href$=".pdf"]')
        pdf_url = urljoin(URL, pdf['href']) if pdf else None
        if pdf_url and urlparse(pdf_url).hostname != 'www.courts.go.jp':
            raise ValueError('Unexpected document host')
        paragraphs = [' '.join(p.get_text(' ', strip=True).split()) for p in cells[0].select('p') if p.get_text(' ', strip=True)]
        rows.append({'category': a.get_text(' ', strip=True), 'summary_lines': paragraphs, 'detail_url': detail, 'pdf_url': pdf_url})
    return {'source_url': r.url, 'source': 'Supreme Court of Japan official website', 'items': rows[:limit], 'returned_list_count': len(rows), 'note': 'Recent Supreme Court judgments listed by the site, ordinarily last three months; not all court decisions. This is the visible HTML list, not an official JSON API or Westlaw Japan.'}
