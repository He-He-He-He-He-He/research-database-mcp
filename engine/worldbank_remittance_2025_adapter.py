"""World Bank RPW 2011–2025 Q3 service-level costs; local official workbook."""
import release_runtime
import datetime
import re
import requests
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095523/rpw_dataset_2011_2025_q3.xlsx'
DOC = 'https://datacatalog.worldbank.org/search/dataset/0037898/remittance-prices-worldwide'

def download(path):
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    with open(path, 'xb') as f:
        f.write(r.content)
    return {'source': URL, 'file': path, 'bytes': len(r.content), 'note': 'Official fixed Q3 2025 workbook; existing files are not overwritten.'}

def query(path, period, origin, destination, offset=0, limit=20):
    if not re.fullmatch('20\\d\\d_[1-4]Q', period):
        raise ValueError('period must be YYYY_1Q to YYYY_4Q')
    if not re.fullmatch('[A-Za-z]{3}', origin) or not re.fullmatch('[A-Za-z]{3}', destination):
        raise ValueError('country codes must be three letters')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    y = int(period[:4])
    q = int(period[5])
    if not (2011, 1) <= (y, q) <= (2025, 3):
        raise ValueError('this snapshot covers 2011 Q1 through 2025 Q3')
    sheet = 'Dataset (up to Q1 2016)' if (y, q) <= (2016, 1) else 'Dataset (from Q2 2016)'
    w = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        it = w[sheet].iter_rows(values_only=True)
        headers = list(next(it))
        end = next((i for i, h in enumerate(headers) if h is None), len(headers))
        headers = headers[:end]
        required = ['id', 'period', 'source_code', 'destination_code', 'cc1 denomination amount', 'cc1 total cost %', 'transparent']
        if not all((x in headers for x in required)) or len(headers) != len(set(headers)):
            raise ValueError('unexpected workbook headers')
        ix = {name: headers.index(name) for name in required}
        matches = 0
        rows = []
        more = False
        for values in it:
            if values[ix['period']] != period or values[ix['source_code']] != origin.upper() or values[ix['destination_code']] != destination.upper():
                continue
            if matches >= offset + limit:
                more = True
                break
            if matches >= offset:
                row = {k: v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v for k, v in zip(headers, values)}
                rows.append(row)
            matches += 1
        return {'source': str(path), 'reference_source': URL, 'catalog': DOC, 'version': None, 'expected_version': '2011–2025 Q3', 'sheet': sheet, 'period': period, 'origin': origin.upper(), 'destination': destination.upper(), 'offset': offset, 'limit': limit, 'has_more': more, 'rows': rows, 'notes': ['Local workbook provenance, version and field definitions are unverified; reference metadata applies only if its identity is confirmed.', 'Service-level observations, not national average or total remittance flows; price collection quarter and sampling matter.', 'cc1/cc2 denomination amount is transaction size in USD; lcu amount and fee use source currency, fx margin and total cost are percentages. Raw fields and missing markers are preserved.', 'Source methodology and definitions changed from Q2 2016; non-transparent services are excluded from the official global average.', 'Workbook last described through Q3 2025, not real-time; local scan may take tens of seconds. If provenance is confirmed, attribute “The World Bank, Remittance Prices Worldwide”.']}
    finally:
        w.close()
