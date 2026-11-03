"""Destatis historical 2025-06 CPI long-series workbook."""
import release_runtime
import hashlib
import io
import openpyxl
import requests
URL = 'https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Verbraucherpreisindex/Publikationen/Downloads-Verbraucherpreise/statistischer-bericht-verbraucherpreisindex-lange-reihen-5611103.xlsx?__blob=publicationFile&v=29'
PAGE = 'https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Verbraucherpreisindex/Publikationen/_publikationen-verbraucherpreisindex.html'
SHEETS = {'annual_index': 'csv-611xx-01', 'annual_change': 'csv-611xx-02', 'monthly_index': 'csv-611xx-03'}
NOTES = ['This is the June 2025 edition of a long-series publication; the current downloadable file and server last-modified timestamp do not prove availability before any particular cutoff.', 'Each row retains original German table headers, geography, statistical series, unit, value, and month. Several series and historical regions occur; select carefully.', 'The annual-change table is percent change, while annual and monthly tables contain index levels with row-specific base years; do not treat indexes as inflation rates.', 'Source symbols such as - are preserved and are not zero. Values may have been revised. Federal Statistical Office permits reproduction with source attribution.']

def query(mode, start, end, keyword='', limit=50, offset=0):
    if mode not in SHEETS or type(start) is not int or type(end) is not int or (not 1900 <= start <= end <= 2100) or (not isinstance(keyword, str)) or (len(keyword) > 100) or (type(limit) is not int) or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid query parameters')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('Destatis did not return XLSX')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    sheet = SHEETS[mode]
    if sheet not in w.sheetnames:
        raise ValueError('Expected Destatis sheet missing')
    vals = w[sheet].iter_rows(values_only=True)
    header = next(vals)
    expected = ('Statistik', 'Gebiet', 'Merkmal_1', 'Merkmal_2', 'Masseinheit', 'Jahr')
    if tuple(header[:6]) != expected or header[-1] != 'Wert':
        raise ValueError('Unexpected Destatis headers')
    rows = []
    for row in vals:
        if not isinstance(row[5], int) or not start <= row[5] <= end:
            continue
        if keyword.casefold() not in ' '.join((str(x or '') for x in row[:4])).casefold():
            continue
        rows.append(dict(zip(header, row)))
    return {'source': URL, 'publication_page': PAGE, 'edition': '2025-06', 'http_last_modified': r.headers.get('Last-Modified'), 'sha256': hashlib.sha256(r.content).hexdigest(), 'sheet': sheet, 'source_headers': header, 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}
