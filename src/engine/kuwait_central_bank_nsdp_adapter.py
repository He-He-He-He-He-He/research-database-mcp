"""Kuwait central bank national summary data: official catalogue and SDMX XML."""
import release_runtime
import re, xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.cbk.gov.kw/en/statistics-and-publication/nsdp'
HOST = 'www.cbk.gov.kw'
MAX = 8000000

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != HOST or u.port or u.username or u.password:
        raise ValueError('only Kuwait central bank HTTPS host')
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
    seen = set()
    for a in soup.find_all('a', href=True):
        if 'download in sdmx' not in a.get_text(' ', strip=True).lower():
            continue
        row = a.find_parent('div', class_='row')
        h = row.find('h5') if row else None
        if not h:
            continue
        title = ' '.join(h.get_text(' ', strip=True).split())
        url = urljoin(PAGE, a['href'])
        u = urlparse(url)
        if u.scheme != 'https' or u.hostname != HOST or u.path != '/en/redirects/download':
            continue
        pair = (title, url)
        if pair in seen:
            continue
        seen.add(pair)
        if query.casefold() in title.casefold():
            out.append({'title': title, 'sdmx': url})
    if not out and (not query):
        raise RuntimeError('official catalogue layout changed')
    return {'source': PAGE, 'matched': len(out), 'datasets': out, 'note': 'Some official links may point to the same dataset under multiple labels; verify series and compiler.'}

def series(title, indicator=None, limit=50, latest=10):
    if not isinstance(title, str) or len(title) > 150:
        raise ValueError('invalid title')
    if indicator is not None and (not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,120}', indicator)):
        raise ValueError('invalid indicator')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(latest, bool) or (not isinstance(latest, int)) or (not 1 <= latest <= 100):
        raise ValueError('limit and latest must be 1-100')
    entries = [x for x in catalogue()['datasets'] if x['title'] == title]
    if len(entries) != 1:
        raise ValueError('title not uniquely present in official catalogue')
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
    return {'catalog_entry': entries[0], 'matching_series': count, 'returned_series': len(results), 'series': results, 'note': 'Complete XML downloaded; observations returned from end in source order. Preserve values, units, frequency and base; confirm actual series content, official producer and recency.'}
