"""MOA reported animal disease statistics. DOC conversion needs macOS textutil."""
import release_runtime
from urllib.parse import urljoin, urlsplit, parse_qs
import os, re, subprocess, tempfile
import requests
from bs4 import BeautifulSoup
BASE = 'https://xmsyj.moa.gov.cn/yqfb/'

def catalog(page=0, keyword=''):
    if not isinstance(page, int) or not 0 <= page <= 5:
        raise ValueError('page must be 0–5')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    url = BASE + ('index.htm' if page == 0 else f'index_{page}.htm')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        title = a.get('title', '') or a.get_text(' ', strip=True)
        target = urljoin(url, a['href'])
        if '全国主要动物疫病报告情况' not in title or keyword not in title or (not re.fullmatch('https://xmsyj\\.moa\\.gov\\.cn/yqfb/\\d{6}/t\\d{8}_\\d+\\.htm', target)):
            continue
        if target not in seen:
            items.append({'title': title, 'url': target})
            seen.add(target)
    return {'source': '农业农村部畜牧兽医局', 'source_url': url, 'items': items}

def table(url):
    match = None
    for p in range(6):
        match = next((x for x in catalog(p)['items'] if x['url'] == url), None)
        if match:
            break
    if not match:
        raise ValueError('URL not found in catalog pages 0–5')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    docs = []
    for a in s.select('a[href]'):
        dest = urljoin(url, a['href'])
        u = urlsplit(dest)
        if u.netloc == 'www.moa.gov.cn' and u.path == '/zxfile/reader':
            dest = parse_qs(u.query).get('file', [''])[0]
        if re.fullmatch('https://xmsyj\\.moa\\.gov\\.cn/yqfb/\\d{6}/P\\d+\\.docx?', dest):
            docs.append(dest)
    docs = list(dict.fromkeys(docs))
    if len(docs) != 1:
        raise ValueError('expected exactly one official DOC attachment')
    r = requests.get(docs[0], timeout=30)
    r.raise_for_status()
    if not (r.content.startswith(bytes.fromhex('d0cf11e0a1b11ae1')) or r.content.startswith(b'PK\x03\x04')):
        raise ValueError('attachment is not DOC or DOCX')
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, 'data.docx' if docs[0].endswith('.docx') else 'data.doc')
        out = os.path.join(d, 'data.html')
        with open(src, 'wb') as f:
            f.write(r.content)
        p = release_runtime.run(['/usr/bin/textutil', '-convert', 'html', '-output', out, src], capture_output=True, timeout=30)
        if p.returncode or not os.path.exists(out):
            raise RuntimeError('macOS textutil DOC conversion failed')
        with open(out, encoding='utf-8') as f:
            html = BeautifulSoup(f.read(), 'html.parser')
    tables = []
    for t in html.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('converted DOC has no HTML tables')
    return {'source': '农业农村部畜牧兽医局', **match, 'attachment_url': docs[0], 'tables': tables}
