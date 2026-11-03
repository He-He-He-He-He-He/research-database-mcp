"""Japanese Supreme Court published judgments: bounded official keyword result list."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
URL = 'https://www.courts.go.jp/hanrei/search2/index.html'

def search(keyword, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must be 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 30):
        raise ValueError('limit must be 1–30')
    r = requests.get(URL, params={'courtCaseType': '1', 'query1': keyword.strip()}, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Unexpected response size')
    soup = BeautifulSoup(r.content, 'html.parser')
    text = soup.get_text(' ', strip=True)
    if '検索結果が2000件を超えました' in text:
        raise ValueError('More than 2000 matches; choose a narrower keyword')
    table = soup.select_one('table.search-result-table')
    if not table:
        if any((x.get_text(' ', strip=True) == '該当する裁判例がありませんでした。' for x in soup.select('#searched'))):
            return {'source_url': r.url, 'keyword': keyword, 'items': [], 'note': 'No matches reported by source; this database is not comprehensive.'}
        raise ValueError('Results table missing; unable to verify zero results')
    rows = []
    for tr in table.select('tr'):
        a = tr.select_one('a[href*="/detail2/"]')
        cells = tr.select('td')
        if not a or not cells:
            continue
        detail = urljoin(URL, a.get('href', ''))
        if urlparse(detail).hostname != 'www.courts.go.jp' or not re.fullmatch('/hanrei/[0-9]+/detail2/index.html', urlparse(detail).path):
            raise ValueError('Unexpected detail link')
        pdf = tr.select_one('a[href$=".pdf"]')
        pdfurl = urljoin(URL, pdf['href']) if pdf else None
        if pdfurl and urlparse(pdfurl).hostname != 'www.courts.go.jp':
            raise ValueError('Unexpected PDF link')
        paragraphs = [' '.join(p.get_text(' ', strip=True).split()) for p in cells[0].select('p') if p.get_text(' ', strip=True)]
        rows.append({'category': a.get_text(' ', strip=True), 'summary_lines': paragraphs, 'detail_url': detail, 'pdf_url': pdfurl})
    return {'source_url': r.url, 'keyword': keyword, 'items': rows[:limit], 'page_item_count': len(rows), 'note': 'First visible page of official Supreme Court decisions matching full-text keyword. Site excludes many judgments. No pagination or full-text retrieval tested; not Westlaw Japan.'}
