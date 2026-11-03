"""Netherlands CPB official World Trade Monitor latest workbook."""
import release_runtime
import hashlib
import io
import re
from urllib.parse import urljoin, urlparse
import requests
import openpyxl
from bs4 import BeautifulSoup
PAGE = 'https://www.cpb.nl/en/worldtrademonitor/latest'
NOTES = ['Latest CPB release is a revised current dataset, not a historical as-of snapshot.', 'Merchandise trade and industrial production figures are indices, not physical shipment volume or trade value. They exclude services; industrial production excludes construction.', 'Always read sheet title and section for base year, seasonal adjustment and weighting; commodity price and unit-value series differ from trade-volume indices.', 'Country and regional aggregates and weights may overlap; estimates and subsequently revised observations are possible.']

def _load():
    r = requests.get(PAGE, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for a in soup.select('a[href]'):
        url = urljoin(r.url, a['href'])
        p = urlparse(url)
        if p.scheme == 'https' and p.hostname == 'www.cpb.nl' and re.fullmatch('/system/files/cpbmedia/CPB-world-trade-monitor-[a-z]+-\\d{4}\\.xlsx', p.path, re.I):
            links.append(url)
    urls = list(dict.fromkeys(links))
    if len(urls) != 1:
        raise ValueError('Could not identify one official CPB workbook')
    r = requests.get(urls[0], timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('CPB workbook is not XLSX')
    return (urls[0], hashlib.sha256(r.content).hexdigest(), openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True))

def _parse(w):
    series = []
    for sheet in ('trade_out', 'inpro_out'):
        if sheet not in w.sheetnames:
            raise ValueError('CPB workbook missing expected sheet')
        s = w[sheet]
        s.reset_dimensions()
        rows = list(s.iter_rows(values_only=True))
        if len(rows) < 8 or 'fixed base' not in str(rows[1][1]):
            raise ValueError('Unexpected CPB worksheet layout')
        dates = list(rows[3][5:])
        dates = [(i + 5, d) for i, d in enumerate(dates) if isinstance(d, str) and re.fullmatch('\\d{4}m(0[1-9]|1[0-2])', d)]
        if not dates:
            raise ValueError('CPB workbook contains no month headings')
        section = None
        weight_label = None
        for row in rows[5:]:
            if len(row) < 3:
                continue
            label, code = (row[1], row[2])
            if label and (not code):
                section = str(label).strip()
                weight_label = row[3] if len(row) > 3 else None
            if not isinstance(code, str) or not re.fullmatch('[a-z0-9_]+', code):
                continue
            series.append({'sheet': sheet, 'sheet_title': rows[1][1], 'workbook_time': rows[3][1], 'section': section, 'weight_label': weight_label, 'weight_or_value': row[3] if len(row) > 3 else None, 'label': str(label).strip(), 'code': code, 'observations': [(d, row[i] if i < len(row) else None) for i, d in dates]})
    return series

def _base():
    url, sha, w = _load()
    return (url, sha, _parse(w))

def catalog(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid filter or pagination')
    url, sha, series = _base()
    k = keyword.casefold()
    rows = [{key: value for key, value in s.items() if key != 'observations'} for s in series if k in (s['label'] + ' ' + s['code'] + ' ' + str(s['section'])).casefold()]
    return {'source': url, 'file_sha256': sha, 'total': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}

def query(code, start, end):
    if not isinstance(code, str) or not re.fullmatch('[a-z0-9_]{3,80}', code):
        raise ValueError('Invalid exact series code')
    if not all((isinstance(x, str) and re.fullmatch('\\d{4}-(0[1-9]|1[0-2])', x) for x in (start, end))) or start > end:
        raise ValueError('Invalid month range')
    url, sha, series = _base()
    matches = [s for s in series if s['code'] == code]
    if len(matches) != 1:
        raise ValueError('Series not found or not unique')
    row = matches[0]
    observations = row.pop('observations')
    row['records'] = [{'month': d[:4] + '-' + d[-2:], 'value': v} for d, v in observations if start <= d[:4] + '-' + d[-2:] <= end]
    return {'source': url, 'file_sha256': sha, 'page': PAGE, 'notes': NOTES, 'series': row}
