"""CMA official early-warning monthly bulletin index and PDF text."""
import release_runtime
import io
import subprocess
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from pypdf import PdfReader
INDEX = 'https://www.cma.gov.cn/zfxxgk/gknr/tfsjyd/yjxxfbqkyb/'

def _valid(url):
    p = urlsplit(url)
    return p.scheme == 'https' and p.netloc == 'www.cma.gov.cn' and p.path.startswith('/zfxxgk/gknr/tfsjyd/yjxxfbqkyb/') and (not p.query) and (not p.fragment)

def _get(url):
    if not _valid(url):
        raise ValueError('not a CMA warning bulletin URL')
    return release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '30', url], capture_output=True, check=True).stdout

def catalogue():
    s = BeautifulSoup(_get(INDEX), 'html.parser')
    rows = []
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        url = urljoin(INDEX, a['href'])
        if '国家突发事件预警信息发布情况月报' in title and _valid(url) and url.endswith('.html'):
            rows.append({'title': title, 'url': url})
    if not rows:
        raise ValueError('CMA catalogue missing')
    return rows

def report(detail_url):
    s = BeautifulSoup(_get(detail_url), 'html.parser')
    links = [urljoin(detail_url, a['href']) for a in s.select('a[href]') if a['href'].lower().endswith('.pdf')]
    links = [u for u in links if _valid(u)]
    if len(links) != 1:
        raise ValueError('PDF link missing or ambiguous')
    data = _get(links[0])
    if not data.startswith(b'%PDF-'):
        raise ValueError('upstream file is not PDF')
    pdf = PdfReader(io.BytesIO(data))
    pages = [p.extract_text() or '' for p in pdf.pages]
    return {'page_url': detail_url, 'pdf_url': links[0], 'pages': pages}
