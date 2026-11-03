"""Read-only official Barbados Statistical Service NSDP SDMX files."""
import release_runtime
import re, xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
PAGE = 'https://stats.gov.bb/wp-content/uploads/2020/12/National-Summary-Data-Page-NSDP.htm'
HOST = 'stats.gov.bb'
MAX = 8000000

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != HOST or u.port or u.username or u.password:
        raise ValueError('only official Barbados statistics HTTPS host')
    with requests.get(url, timeout=30, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.status_code != 200:
            raise RuntimeError('unexpected response status')
        pieces = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > MAX:
                raise RuntimeError('response exceeds 8 MB')
            pieces.append(c)
    return b''.join(pieces)

def catalogue(query=''):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError('invalid query')
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    out = []
    for row in soup.find_all('tr'):
        cells = row.find_all('td', recursive=False)
        if not cells:
            continue
        for a in row.find_all('a', href=True):
            u = urlparse(a['href'])
            if u.scheme != 'https' or u.hostname != HOST or (not re.fullmatch('/nsdp/xml/[A-Za-z0-9_]+\\.xml', u.path)):
                continue
            title = ' '.join(cells[0].get_text(' ', strip=True).split())
            ident = u.path.rsplit('/', 1)[-1][:-4]
            if query.casefold() in (title + ' ' + ident).casefold():
                out.append({'title': title, 'dataset': ident, 'sdmx': a['href']})
    if not out and (not query):
        raise RuntimeError('official catalogue layout changed')
    return {'source': PAGE, 'matched': len(out), 'datasets': out, 'note': 'Catalogue labels may differ from actual XML contents; verify each series and producer.'}

def series(dataset, indicator=None, limit=50, latest=10):
    if not isinstance(dataset, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', dataset):
        raise ValueError('invalid dataset')
    if indicator is not None and (not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,120}', indicator)):
        raise ValueError('invalid indicator')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(latest, bool) or (not isinstance(latest, int)) or (not 1 <= latest <= 100):
        raise ValueError('limit and latest must be 1-100')
    entries = [x for x in catalogue()['datasets'] if x['dataset'] == dataset]
    if len(entries) != 1:
        raise ValueError('dataset is not uniquely present in official catalogue')
    root = ET.fromstring(_get(entries[0]['sdmx']))
    results = []
    count = 0
    for e in root.iter():
        if e.tag.split('}')[-1] != 'Series' or (indicator and e.attrib.get('INDICATOR') != indicator):
            continue
        count += 1
        if len(results) < limit:
            obs = [x.attrib for x in e if x.tag.split('}')[-1] == 'Obs']
            results.append({'attributes': e.attrib, 'observation_count': len(obs), 'observations': obs[-latest:]})
    return {'catalog_entry': entries[0], 'matching_series': count, 'returned_series': len(results), 'series': results, 'note': 'XML full download, last observations in source order; preserve original values, frequency, base period and unit multiplier. The Population catalogue currently points to an apparent labour force indicator; verify definitions against original source.'}
