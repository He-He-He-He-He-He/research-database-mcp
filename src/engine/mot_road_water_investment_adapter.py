"""Official provincial road and waterway transport fixed investment workbooks."""
import release_runtime
import io, re, hashlib
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
from openpyxl import load_workbook
BASE = 'https://www.mot.gov.cn/shuju/tongjishuju/gudingzctz/'

def _get(u, maxbytes):
    with requests.get(u, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > maxbytes:
                raise ValueError('source too large')
        return bytes(b)

def catalog(page=0, keyword=''):
    if type(page) is not int or not 0 <= page <= 4:
        raise ValueError('page must be 0–4')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    u = BASE + ('index.html' if page == 0 else f'index_{page}.html')
    s = BeautifulSoup(_get(u, 5000000), 'html.parser')
    out = []
    seen = set()
    for a in s.select('.news-item a[href]'):
        u = urljoin(BASE, a['href'])
        v = urlsplit(u)
        title = ' '.join(a.get_text(' ', strip=True).split())
        if v.scheme != 'https' or v.netloc != 'xxgk.mot.gov.cn' or (not re.fullmatch('/jigou/zhghs/\\d{6}/t\\d+_\\d+\\.html', v.path)) or v.query or v.fragment or (u in seen):
            continue
        if '公路水路交通固定资产投资完成情况' not in title:
            continue
        seen.add(u)
        if keyword in title:
            out.append({'title': title, 'url': u})
    if not seen:
        raise ValueError('official index unavailable or changed')
    return {'page': page, 'page_count': 5, 'page_entries': len(seen), 'items': out, 'source': '交通运输部公路水路固定资产投资目录'}

def table(page, url, region=''):
    if not isinstance(region, str) or len(region) > 100:
        raise ValueError('invalid region')
    entry = next((x for x in catalog(page)['items'] if x['url'] == url), None)
    if not entry:
        raise ValueError('URL not in selected official index page')
    s = BeautifulSoup(_get(url, 5000000), 'html.parser')
    attachments = set()
    for a in s.select('a[href]'):
        h = urljoin(url, a['href'])
        v = urlsplit(h)
        if v.scheme == 'https' and v.netloc == 'xxgk.mot.gov.cn' and re.fullmatch('/jigou/zhghs/\\d{6}/P\\d+\\.xlsx', v.path) and (not v.query) and (not v.fragment):
            attachments.add(h)
    if len(attachments) != 1:
        raise ValueError('no unique XLSX attachment; older reports may be PDF')
    link = attachments.pop()
    raw = _get(link, 15000000)
    if not raw.startswith(b'PK\x03\x04'):
        raise ValueError('not an XLSX workbook')
    w = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    if '公路水路投资额' not in w.sheetnames:
        raise ValueError('expected investment worksheet missing')
    sh = w['公路水路投资额']
    values = list(sh.iter_rows(max_col=7, values_only=True))
    w.close()
    if len(values) < 10 or '公路水路交通固定资产投资完成情况' not in str(values[0][0]):
        raise ValueError('unexpected table layout')
    records = []
    notes = []
    for n, row in enumerate(values[5:], 6):
        label = row[0]
        if not isinstance(label, str) or not label.strip():
            continue
        if label.strip().startswith(('注：', '注:')):
            notes.append(label.strip())
            continue
        if ''.join(region.split()) in ''.join(label.split()):
            records.append({'row': n, 'region': label, 'values': list(row[1:])})
    return {'title': entry['title'], 'source_page': url, 'workbook_url': link, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheet': '公路水路投资额', 'headers': [list(x) for x in values[:5]], 'rows': records, 'notes': notes, 'note': '累计金额单位万元；同比为百分比。公路水路建设、其中公路和水运分别两列，保留原表空值；年初累计不是单月，历史目录有PDF而非XLSX。'}
