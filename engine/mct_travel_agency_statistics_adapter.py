"""MCT travel agency statistical DOCX tables republished by China Tourism News."""
import release_runtime
import io, zipfile
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
import requests
from bs4 import BeautifulSoup
ARTICLES = {'2022': 'https://www.ctnews.com.cn/xxk/tzgg/content/2023-04/28/content_141444.html', '2024q2': 'https://www.ctnews.com.cn/jujiao/content/2024-09/04/content_164297.html'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def catalog(period):
    if period not in ARTICLES:
        raise ValueError('period must be 2022 or 2024q2')
    url = ARTICLES[period]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        href = urljoin(url, a['href'])
        title = a.get_text(' ', strip=True)
        if href.startswith('https://www.ctnews.com.cn/') and href.lower().endswith('.docx') and (href not in seen):
            items.append({'title': title, 'url': href})
            seen.add(href)
    if not items:
        raise ValueError('no DOCX attachments found')
    return {'period': period, 'publisher': '中国旅游新闻网转载文化和旅游部资料', 'article_url': url, 'items': items}

def table(period, url):
    match = next((item for item in catalog(period)['items'] if item['url'] == url), None)
    if not match:
        raise ValueError('URL is not in the selected article attachments')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'PK\x03\x04'):
        raise ValueError('response is not DOCX')
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        info = z.getinfo('word/document.xml')
        if info.file_size > 10 * 1024 * 1024:
            raise ValueError('document XML exceeds size limit')
        root = ET.fromstring(z.read(info))
    result = []
    for tbl in root.iter(W + 'tbl'):
        rows = []
        for tr in tbl.findall(W + 'tr'):
            row = []
            for tc in tr.findall(W + 'tc'):
                text = ''.join((t.text or '' for t in tc.iter(W + 't')))
                props = tc.find(W + 'tcPr')
                span = props.find(W + 'gridSpan') if props is not None else None
                merge = props.find(W + 'vMerge') if props is not None else None
                row.append({'text': text, 'colspan': int(span.get(W + 'val', '1')) if span is not None else 1, 'vertical_merge': None if merge is None else merge.get(W + 'val', 'continue')})
            if row:
                rows.append(row)
        if rows:
            result.append(rows)
    if not result:
        raise ValueError('DOCX has no tables')
    return {'period': period, 'publisher': '中国旅游新闻网转载文化和旅游部资料', 'source_article': ARTICLES[period], **match, 'tables': result}
