"""Jiangmen 2025 official yearbook chapter PDF catalog and text."""
import release_runtime
import io
import subprocess
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from pypdf import PdfReader
INDEX = 'https://www.jiangmen.gov.cn/bmpd/jmstjj/tjsj/tjnj/content/post_3445439.html'

def _get(url):
    return release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '45', url], capture_output=True, check=True, timeout=50).stdout

def catalog(keyword=''):
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        href = urljoin(INDEX, a['href'])
        u = urlparse(href)
        if u.hostname == 'www.jiangmen.gov.cn' and u.path.startswith('/attachment/') and u.path.lower().endswith('.pdf') and (''.join(keyword.split()) in ''.join(title.split())):
            url = urlunparse(('https', u.netloc, u.path, u.params, u.query, u.fragment))
            items.append({'title': title, 'url': url})
    if not items and (not keyword):
        raise ValueError('official chapter catalog missing')
    return items

def pages(chapter, keyword=''):
    items = [x for x in catalog() if x['title'] == chapter]
    if len(items) != 1:
        raise ValueError('chapter missing or ambiguous')
    item = items[0]
    raw = _get(item['url'])
    if not raw.startswith(b'%PDF'):
        raise ValueError('official response not PDF')
    document = PdfReader(io.BytesIO(raw))
    result = []
    for n, page in enumerate(document.pages, 1):
        text = page.extract_text() or ''
        if keyword in text:
            result.append({'pdf_page': n, 'text': text})
    if not keyword and (not any((x['text'].strip() for x in result))):
        raise ValueError('no extractable text')
    return {'source': '江门市统计局《江门统计年鉴2025》', 'source_url': item['url'], 'catalog_url': INDEX, 'chapter': chapter, 'page_count': len(document.pages), 'pages': result}
