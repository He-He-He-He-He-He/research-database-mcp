"""MCT travel agency statistical DOCX tables republished by China Tourism News."""
import release_runtime
import io, zipfile
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
import requests
from bs4 import BeautifulSoup
ARTICLES = {'2023q1': 'https://www.ctnews.com.cn/xxk/tzgg/content/2023-05/30/content_142799.html', '2024q1': 'https://www.ctnews.com.cn/baogao/content/2024-06/26/content_161812.html'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def _get(url):
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 10000000:
                raise ValueError('source too large')
        return bytes(data)

def catalog(period):
    if period not in ARTICLES:
        raise ValueError('period must be 2023q1 or 2024q1')
    url = ARTICLES[period]
    s = BeautifulSoup(_get(url), 'html.parser')
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
    data = _get(url)
    if not data.startswith(b'PK\x03\x04'):
        raise ValueError('response is not DOCX')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
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
    return {'period': period, 'publisher': '中国旅游新闻网转载文化和旅游部资料', 'source_article': ARTICLES[period], **match, 'tables': result, 'note': '季度旅行社调查的填报或审核范围按原报告说明；人次、人天、组织、外联和接待为不同指标，不代表全部出游或入境人数。'}
