"""Official MOT port throughput PDF directory and table rows."""
import release_runtime
import re
import io
import contextlib
import openpyxl
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import fitz
CATALOG = 'https://www.mot.gov.cn/shuju/tongjishuju/gangkoutuntuliang/'

def catalog(keyword=''):
    r = requests.get(CATALOG, timeout=25)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    result = []
    seen = set()
    for a in BeautifulSoup(r.text, 'html.parser').find_all('a', href=True):
        title = a.get_text(' ', strip=True)
        url = urljoin(CATALOG, a['href'])
        if '吞吐量' in title and keyword in title and (urlparse(url).hostname == 'xxgk.mot.gov.cn') and (url not in seen):
            seen.add(url)
            result.append({'title': title, 'url': url})
    return result

def read(url, keyword='', limit=100):
    if urlparse(url).scheme != 'https' or urlparse(url).hostname != 'xxgk.mot.gov.cn':
        raise ValueError('只接受交通运输部公开详情页')
    if not 1 <= int(limit) <= 500:
        raise ValueError('limit 为 1–500')
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    s = BeautifulSoup(r.text, 'html.parser')
    pdfs = []
    for a in s.find_all('a', href=True):
        u = urljoin(url, a['href'])
        if urlparse(u).hostname == 'xxgk.mot.gov.cn' and urlparse(u).path.lower().endswith(('.pdf', '.xlsx')) and (u not in pdfs):
            pdfs.append(u)
    if len(pdfs) != 1:
        raise RuntimeError('没有唯一的官方 PDF 或 XLSX 附件')
    d = requests.get(pdfs[0], timeout=35)
    d.raise_for_status()
    if pdfs[0].lower().endswith('.xlsx'):
        if not d.content.startswith(b'PK\x03\x04'):
            raise RuntimeError('附件不是 XLSX')
        book = openpyxl.load_workbook(io.BytesIO(d.content), data_only=True, read_only=True)
        ws = book.active
        allrows = []
        for values in ws.iter_rows(values_only=True):
            row = list(values)
            while row and row[-1] is None:
                row.pop()
            allrows.append(row)
        book.close()
        selected = [{'row': i + 1, 'cells': row} for i, row in enumerate(allrows) if not keyword or any((keyword in re.sub('\\s+', '', str(v)) for v in row if v is not None))]
        return {'source_url': url, 'attachment_url': pdfs[0], 'format': 'xlsx', 'sheet': ws.title, 'headers': allrows[:6], 'matches': len(selected), 'rows': selected[:int(limit)], 'note': '原始单元格与空值保留；吞吐量为年初累计。'}
    if not d.content.startswith(b'%PDF-'):
        raise RuntimeError('附件不是 PDF')
    doc = fitz.open(stream=d.content, filetype='pdf')
    rows = []
    headers = []
    notes = []
    for n, p in enumerate(doc):
        notes.append(p.get_text())
        with contextlib.redirect_stdout(io.StringIO()):
            tables = p.find_tables().tables
        for table in tables:
            for i, row in enumerate(table.extract()):
                if i < 6:
                    headers.append({'page': n + 1, 'row': i + 1, 'cells': row})
                if keyword and any((keyword in re.sub('\\s+', '', str(v)) for v in row if v is not None)):
                    rows.append({'page': n + 1, 'row': i + 1, 'cells': row})
                elif not keyword:
                    rows.append({'page': n + 1, 'row': i + 1, 'cells': row})
    doc.close()
    return {'source_url': url, 'pdf_url': pdfs[0], 'headers': headers, 'matches': len(rows), 'rows': rows[:int(limit)], 'page_text': notes, 'note': 'PDF 自动识别表格应与原件核对，保留空白，不视为零；吞吐量为年初累计。'}
