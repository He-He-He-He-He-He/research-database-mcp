"""IPPC official index of adopted phytosanitary standards and annexes."""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.ippc.int/en/core-activities/standards-setting/ispms/'
NOTES = ['Rows include standards, diagnostic protocols and other annexes: the count of rows is not the count of distinct adopted ISPMs.', 'Publication date is the web entry publication date and not necessarily initial adoption, revision, or entry into force.', 'Current listings and linked translations can differ in revision or language; current text does not establish historical applicability. ISPM 30 is identified as revoked in the source overview.', 'National implementation, import requirements and legal effect must be checked with the relevant national plant protection organization. Links are source-provided and some are HTTP.', 'No inference that a missing item is revoked, applicable, or absent from all sources.']

def search(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid keyword or pagination')
    r = requests.get(PAGE, timeout=60)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    table = s.select_one('table#publications')
    if not table or not table.tbody:
        raise ValueError('IPPC catalogue table missing')
    rows = []
    for tr in table.tbody.find_all('tr', recursive=False):
        td = tr.find_all('td', recursive=False)
        if len(td) < 4:
            raise ValueError('Unexpected IPPC catalogue row')
        a = td[1].find('a', href=True)
        if not a:
            raise ValueError('IPPC publication link missing')
        ref = td[0].get_text(' ', strip=True)
        title = a.get_text(' ', strip=True)
        if not title:
            raise ValueError('Unexpected blank IPPC title')
        links = {}
        for node in td[3].find_all('a', href=True):
            language = node.get_text(' ', strip=True)
            if language in ('EN', 'FR', 'ES', 'AR', 'ZH', 'RU'):
                links[language] = urljoin(PAGE, node['href'])
        rows.append({'reference': ref, 'title': title, 'publication_date_raw': td[2].get_text(' ', strip=True), 'publication_page': urljoin(PAGE, a['href']), 'language_links': links})
    if not rows:
        raise ValueError('Empty IPPC catalogue')
    matches = [row for row in rows if keyword.casefold() in (row['reference'] + ' ' + row['title']).casefold()]
    return {'source': PAGE, 'total_source_rows': len(rows), 'total_matching': len(matches), 'offset': offset, 'notes': NOTES, 'records': matches[offset:offset + limit]}
