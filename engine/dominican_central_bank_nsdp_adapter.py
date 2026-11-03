"""Dominican central bank NSDP catalogue and official central bank SDMX files."""
import release_runtime
import re, xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.bancentral.gov.do/a/CustomView/4158-national-summary-data-page-nsdp'
HOSTS = {'www.bancentral.gov.do', 'cdn.bancentral.gov.do'}
MAX = 8000000

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname not in HOSTS or u.port or u.username or u.password:
        raise ValueError('only official central bank HTTPS hosts')
    with requests.get(url, timeout=30, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.status_code != 200:
            raise RuntimeError('unexpected response status')
        size = 0
        chunks = []
        for c in r.iter_content(65536):
            size += len(c)
            if size > MAX:
                raise RuntimeError('response exceeds 8 MB')
            chunks.append(c)
    return b''.join(chunks)

def catalogue(query=''):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError('invalid query')
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    out = []
    for row in soup.find_all('tr'):
        cells = row.find_all(['td', 'th'], recursive=False)
        if not cells:
            continue
        title = ' '.join(cells[0].get_text(' ', strip=True).split())
        for a in row.find_all('a', href=True):
            url = urljoin(PAGE, a['href'])
            u = urlparse(url)
            if u.scheme != 'https' or u.hostname != 'cdn.bancentral.gov.do' or (not u.path.startswith('/documents/nsdp/documents/')) or (not u.path.lower().endswith('.xml')):
                continue
            if query.casefold() in title.casefold():
                out.append({'title': title, 'sdmx': url})
    if not out and (not query):
        raise RuntimeError('official catalogue layout changed')
    return {'source': PAGE, 'matched': len(out), 'datasets': out, 'note': 'Only official central-bank CDN XML; ministry and other hosts on the page are not accessed. Check data compiler and definitions.'}

def series(title, indicator=None, limit=50, latest=10):
    if not isinstance(title, str) or len(title) > 150:
        raise ValueError('invalid title')
    if indicator is not None and (not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,120}', indicator)):
        raise ValueError('invalid indicator')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(latest, bool) or (not isinstance(latest, int)) or (not 1 <= latest <= 100):
        raise ValueError('limit and latest must be 1-100')
    entries = [x for x in catalogue()['datasets'] if x['title'] == title]
    if len(entries) != 1:
        raise ValueError('title not uniquely present in central-bank catalogue')
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
    return {'catalog_entry': entries[0], 'matching_series': count, 'returned_series': len(results), 'series': results, 'note': 'Complete XML fetched; last observations in source order. Preserve original strings, frequency, base and multiplier; check indicator definitions, status and compilation source.'}
