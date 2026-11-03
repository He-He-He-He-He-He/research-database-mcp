"""FHFA quarterly state all-transactions house-price indexes, source CSV."""
import release_runtime
import csv
import hashlib
import io
import re
import requests
URL = 'https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv'
INFO = 'https://www.fhfa.gov/data/hpi/datasets'
STATES = frozenset('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())

def query(state, start_year=1975, end_year=2100):
    if not isinstance(state, str) or state.upper() not in STATES:
        raise ValueError('Use a valid two-letter US state or DC code')
    state = state.upper()
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (start_year, end_year))) or not 1975 <= start_year <= end_year <= 2100:
        raise ValueError('Invalid year interval')
    with requests.get(URL, timeout=30, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('FHFA data request failed: HTTP ' + str(response.status_code))
        content = bytearray()
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            if len(content) > 2000000:
                raise RuntimeError('Unexpectedly large FHFA CSV')
    try:
        rows = list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
    except UnicodeError:
        raise RuntimeError('Unexpected FHFA CSV encoding') from None
    if not rows:
        raise RuntimeError('Empty FHFA CSV')
    items = []
    for row in rows:
        if len(row) != 4 or row[0] not in STATES or (not re.fullmatch('\\d{4}', row[1])) or (row[2] not in ('1', '2', '3', '4')) or (not re.fullmatch('\\d+(?:\\.\\d+)?', row[3])):
            raise RuntimeError('Unexpected FHFA CSV row; format may have changed')
        if row[0] == state and start_year <= int(row[1]) <= end_year:
            items.append({'state': row[0], 'year': int(row[1]), 'quarter': int(row[2]), 'index_original': row[3]})
    return {'source': 'FHFA House Price Index, all-transactions, quarterly states', 'source_url': URL, 'source_information': INFO, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes_downloaded': len(content), 'selection': {'state': state, 'start_year': start_year, 'end_year': end_year}, 'returned': len(items), 'items': items, 'note': '1980年第一季度=100；未季节调整。单户住宅全交易指数含购买和再融资估值，覆盖有条件的贷款样本；是指数，不是房价金额或直接涨跌幅，可修订。空结果不代表零。'}
