"""Justice Canada consolidated legislation alphabetical index and XML originals."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
BASE = 'https://laws-lois.justice.gc.ca'

def _get(url):
    r = requests.get(url, timeout=40, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    return r

def catalogue(letter, kind='acts', query=''):
    if kind not in ('acts', 'regulations') or not isinstance(letter, str) or (not re.fullmatch('[A-Za-z]', letter)):
        raise ValueError('kind must be acts or regulations; letter must be A–Z')
    url = f'{BASE}/eng/{kind}/{letter.upper()}.html'
    soup = BeautifulSoup(_get(url).content, 'html.parser')
    results = []
    for a in soup.select('a.TocTitle[href]'):
        name = a.get_text(' ', strip=True)
        if query.casefold() not in name.casefold():
            continue
        link = urljoin(url, a['href'])
        parsed = urlsplit(link)
        if parsed.scheme == 'https' and parsed.netloc == 'laws-lois.justice.gc.ca' and parsed.path.startswith(f'/eng/{kind}/') and parsed.path.endswith('/index.html'):
            results.append({'title': name, 'url': link})
    return results

def document(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'laws-lois.justice.gc.ca' or (not re.fullmatch('/eng/(acts|regulations)/[^/]+/index\\.html', parsed.path)) or parsed.query or parsed.fragment:
        raise ValueError('expected a Justice Canada legislation index URL')
    soup = BeautifulSoup(_get(url).content, 'html.parser')
    xml_links = [urljoin(url, a['href']) for a in soup.select('a[href]') if 'XML Full Document' in a.get_text(' ', strip=True)]
    if len(xml_links) != 1:
        raise ValueError('official XML link missing or ambiguous')
    x = urlsplit(xml_links[0])
    if x.scheme != 'https' or x.netloc != 'laws-lois.justice.gc.ca' or (not x.path.startswith('/eng/XML/')) or (not x.path.endswith('.xml')):
        raise ValueError('unexpected XML link')
    body = _get(xml_links[0]).content
    root = ET.fromstring(body)
    return {'index_url': url, 'xml_url': xml_links[0], 'xml': body.decode('utf-8'), 'root_attributes': root.attrib}
