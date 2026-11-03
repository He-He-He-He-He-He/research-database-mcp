"""Global Environment Facility publicly indexed project catalogue webpage."""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
URL = 'https://www.thegef.org/projects-operations/database'

def search(keyword='', page=0):
    if not isinstance(page, int) or isinstance(page, bool) or page < 0:
        raise ValueError('page must be a nonnegative integer')
    p = {'page': page}
    if keyword:
        p['project_search'] = keyword
    r = requests.get(URL, params=p, timeout=45)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    table = s.find('table')
    if not table:
        raise ValueError('project table missing')
    headers = [v.get_text(' ', strip=True) for v in table.select('thead th')]
    expected = ['Title', 'ID', 'Countries', 'Focal Areas', 'Type', 'Agencies', 'GEF Grant', 'Cofinancing', 'Status']
    if headers != expected:
        raise ValueError('unexpected project table schema')
    rows = []
    for tr in table.select('tbody tr'):
        cells = tr.select('td')
        if len(cells) != len(headers):
            raise ValueError('unexpected project row')
        row = {k: v.get_text(' ', strip=True) for k, v in zip(headers, cells)}
        a = cells[0].find('a', href=True)
        row['url'] = urljoin(URL, a['href']) if a else None
        rows.append(row)
    links = [urljoin(URL, a['href']) for a in s.select('a[rel="next"]') if a.has_attr('href')]
    return {'source': URL, 'request': p, 'headers': headers, 'rows': rows, 'next': links[0] if links else None, 'notes': ['Official catalogue webpage with source search and zero-based pagination; results are one page only, and source search scope may include fields other than country.', 'Grant and cofinancing are preserved as displayed strings; individual project details describe Financials in USD. Missing amounts are not zero and financing is not automatically disbursed.', 'Status may be concept approval rather than implementation; multinational project values must not be attributed in full to each country. No independent source snapshot timestamp was observed.']}
