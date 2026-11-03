"""US Supreme Court published opinion term tables; no full-text search."""
import release_runtime
import datetime
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.supremecourt.gov'

def opinions(term, keyword=''):
    if isinstance(term, bool) or not isinstance(term, int) or (not 2018 <= term <= datetime.date.today().year):
        raise ValueError('term must be 2018 through the current year')
    url = f'{BASE}/opinions/slipopinion/{term % 100:02d}'
    response = requests.get(url, timeout=40, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = []
    for table in soup.select('table.table.table-bordered'):
        headers = [x.get_text(' ', strip=True) for x in table.select('tr:first-child th')]
        if headers != ['R-', 'Date', 'Docket', 'Name', 'J.', 'Citation']:
            continue
        for tr in table.select('tr')[1:]:
            cells = tr.find_all('td', recursive=False)
            if len(cells) != 6:
                continue
            a = cells[3].find('a', href=True)
            if not a:
                continue
            entry = {'number': cells[0].get_text(' ', strip=True), 'date': cells[1].get_text(' ', strip=True), 'docket': cells[2].get_text(' ', strip=True), 'name': a.get_text(' ', strip=True), 'justice': cells[4].get_text(' ', strip=True), 'citation': cells[5].get_text(' ', strip=True), 'pdf_url': urljoin(BASE, a['href']), 'source_url': url}
            if keyword.casefold() in ' '.join([entry['name'], entry['docket']]).casefold():
                rows.append(entry)
    if not soup.select('table.table.table-bordered'):
        raise ValueError('No opinion table found; upstream page may have changed')
    return rows

def read_pdf(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != 'www.supremecourt.gov' or (not p.path.startswith('/opinions/')) or (not p.path.lower().endswith('.pdf')) or p.query or p.fragment:
        raise ValueError('expected US Supreme Court opinion PDF URL')
    r = requests.get(url, timeout=40)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return r.content
