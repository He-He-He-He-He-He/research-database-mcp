"""MWR historical water resources report original PDFs and page text."""
import release_runtime
import io, re, subprocess
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from pypdf import PdfReader
BASE = 'https://slqjd.mwr.gov.cn/'
PAGES = {2012: 'szygb/2020-03-20/173.html', 2013: 'szygb/2020-03-20/172.html', 2019: 'szygb/2021-03-31/296.html', 2020: 'szygb/2022-09-23/332.html'}

def _get(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != 'slqjd.mwr.gov.cn' or p.query or p.fragment:
        raise ValueError('unexpected source URL')
    return release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '45', url], capture_output=True, check=True).stdout

def catalogue():
    return [{'year': y, 'viewer_url': BASE + p} for y, p in PAGES.items()]

def report(year):
    if isinstance(year, bool) or year not in PAGES:
        raise ValueError('available years: 2012, 2013, 2019, 2020')
    viewer = BASE + PAGES[year]
    content = _get(viewer)
    soup = BeautifulSoup(content, 'html.parser')
    if not soup.find('h3') or f'{year}年中国水资源公报' not in soup.find('h3').get_text(' ', strip=True):
        raise ValueError('viewer title does not match requested year')
    m = re.search("var DEFAULT_URL\\s*=\\s*'([^']+)'", content.decode('utf-8', 'replace'))
    if not m:
        raise ValueError('PDF URL not found')
    url = m.group(1)
    parsed = urlsplit(url)
    if not parsed.path.startswith('/upload/') or not parsed.path.lower().endswith('.pdf'):
        raise ValueError('unexpected PDF path')
    pdf = _get(url)
    if not pdf.startswith(b'%PDF-'):
        raise ValueError('not PDF')
    reader = PdfReader(io.BytesIO(pdf))
    return {'year': year, 'viewer_url': viewer, 'pdf_url': url, 'pages': [p.extract_text() or '' for p in reader.pages]}
