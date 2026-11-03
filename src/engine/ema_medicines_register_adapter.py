"""European Medicines Agency current medicines export."""
import release_runtime
import datetime
import hashlib
import io
import requests
import openpyxl
URL = 'https://www.ema.europa.eu/en/documents/report/medicines-output-medicines-report_en.xlsx'
PAGE = 'https://www.ema.europa.eu/en/medicines/download-medicine-data'
NOTES = ['EMA medicine export includes different regulatory outcomes, including authorised, withdrawn, refused and revoked items. Inspect medicine and opinion status and relevant dates in each row.', 'This is not a list of all medicines available in Europe, a treatment recommendation, or proof that a drug is approved or available in any particular country.', 'Current records and URLs can change; a past decision date does not prove that all present information existed at that date. Consult the current EMA product information and competent national authority.', 'Therapeutic indications and dates are reproduced as source data, without assessing current clinical suitability.']

def search(keyword, category='', limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (category not in ('', 'Human', 'Veterinary')) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid query')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('EMA did not return an XLSX workbook')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    if 'Medicine' not in w.sheetnames:
        raise ValueError('Unexpected EMA workbook')
    s = w['Medicine']
    meta = next(s.iter_rows(min_row=1, max_row=1, max_col=4, values_only=True))
    header = next(s.iter_rows(min_row=9, max_row=9, max_col=39, values_only=True))
    if header[:4] != ('Category', 'Name of medicine', 'EMA product number', 'Medicine status') or header[38] != 'Medicine URL':
        raise ValueError('Unexpected EMA column headings')
    matches = []
    term = keyword.casefold()
    for row in s.iter_rows(min_row=10, max_col=39, values_only=True):
        if not row[1] or (category and row[0] != category):
            continue
        if term not in ' '.join((str(row[i] or '') for i in (1, 2, 6, 7))).casefold():
            continue
        matches.append([v.isoformat() if isinstance(v, (datetime.datetime, datetime.date)) else v for v in row])
    return {'source': URL, 'page': PAGE, 'workbook_timestamp_raw': meta[3], 'http_last_modified': r.headers.get('Last-Modified'), 'sha256': hashlib.sha256(r.content).hexdigest(), 'columns': header, 'total_matching': len(matches), 'offset': offset, 'notes': NOTES, 'records': matches[offset:offset + limit]}
