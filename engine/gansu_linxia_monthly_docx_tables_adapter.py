"""Official Linxia (Gansu) monthly indicators DOCX tables."""
import release_runtime
import io, re, zipfile, xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
INDEX = 'https://linxia.gov.cn/lxz/zwgk/fdzdgknr/tjsj/tjyb/index.html'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'

def catalog():
    r = requests.get(INDEX, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    seen = set()
    for a in s.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        url = urljoin(INDEX, a['href'])
        p = urlsplit(url)
        if re.fullmatch('\\d{4}年1-\\d{1,2}月临夏州主要指标完成情况表\\.docx', title) and p.scheme == 'https' and (p.netloc == 'linxia.gov.cn') and (p.path == '/api-gateway/jpaas-web-server/front/document/download') and (url not in seen):
            out.append({'title': title, 'url': url})
            seen.add(url)
    if not out:
        raise ValueError('no monthly DOCX attachments found')
    return {'source': '临夏回族自治州人民政府统计月报', 'catalog_url': INDEX, 'scope': '当前列表中直接可见附件', 'items': out}

def tables(url):
    if not isinstance(url, str) or url not in {x['url'] for x in catalog()['items']}:
        raise ValueError('URL must appear in the current official catalog')
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK\x03\x04'):
        raise ValueError('attachment is not DOCX')
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        info = z.getinfo('word/document.xml')
        if info.file_size > 20000000:
            raise ValueError('document XML too large')
        root = ET.fromstring(z.read(info))
    result = []
    for t in root.findall('.//w:tbl', NS):
        rows = []
        for tr in t.findall('./w:tr', NS):
            row = []
            for tc in tr.findall('./w:tc', NS):
                props = tc.find('./w:tcPr', NS)
                span = props.find('./w:gridSpan', NS) if props is not None else None
                merge = props.find('./w:vMerge', NS) if props is not None else None
                row.append({'text': ''.join((x.text or '' for x in tc.findall('.//w:t', NS))), 'grid_span': int(span.get(W + 'val', '1')) if span is not None else 1, 'vertical_merge': None if merge is None else merge.get(W + 'val', 'continue')})
            if row:
                rows.append(row)
        if rows:
            result.append(rows)
    if not result:
        raise ValueError('DOCX contains no tables')
    return {'source': '临夏回族自治州人民政府统计月报', 'catalog_url': INDEX, 'url': url, 'tables': result}
