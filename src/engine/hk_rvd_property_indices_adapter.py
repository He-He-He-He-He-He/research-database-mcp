"""Hong Kong RVD monthly property price and rental index source tables."""
import release_runtime
import csv
import hashlib
import io
import re
import requests
BASE = 'https://www.rvd.gov.hk/datagovhk/'
FILES = {'residential_rent': '1.3M.csv', 'residential_price': '1.4M.csv', 'office_rent': '2.3M.csv', 'office_price': '2.4M.csv', 'office_core': '2.5M.csv', 'retail': '3.2M.csv'}
NOTES = ['Indices are not transaction prices, rents in currency units, or yields. The RVD monthly supplement identifies the relevant indices with base 1999=100.', 'The series cover different premises, classes and geographies; source column titles and remark fields are retained. Primary sales are excluded from the domestic price index.', 'P indicates provisional. For office_core, Y indicates fewer than 10 transactions; other flags such as Z vary by field, so check the official data dictionary.', 'Current data can be revised; an observation month is not a historical publication snapshot.']

def query(kind, start, end):
    if kind not in FILES or not all((isinstance(v, str) and re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', v) for v in (start, end))) or start > end:
        raise ValueError('Invalid index or date range')
    url = BASE + FILES[kind]
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    reader = csv.reader(io.StringIO(r.content.decode('utf-8-sig')))
    rows = list(reader)
    if len(rows) < 3 or not rows[0] or (not rows[0][0].startswith('PRIVATE')) or (not rows[1]) or (rows[1][0] != 'Month'):
        raise ValueError('Unexpected RVD CSV')
    head = rows[1]
    result = []
    for row in rows[2:]:
        if not row or not row[0].strip():
            continue
        if len(row) != len(head):
            raise ValueError('Unexpected RVD row width')
        m = re.fullmatch('(0[1-9]|1[0-2])-(\\d{4})', row[0])
        if not m:
            raise ValueError('Unexpected RVD month')
        month = m[2] + '-' + m[1]
        if start <= month <= end:
            result.append({'month': month, 'cells_raw': row})
    return {'source': url, 'dataset_page': 'https://data.gov.hk/tc-data/dataset/hk-rvd-tsinfo_rvd-property-market-statistics', 'data_dictionary': BASE + 'Data_Dic.pdf', 'source_title': rows[0][0], 'columns': head, 'http_last_modified': r.headers.get('Last-Modified'), 'sha256': hashlib.sha256(r.content).hexdigest(), 'notes': NOTES, 'records': result}
