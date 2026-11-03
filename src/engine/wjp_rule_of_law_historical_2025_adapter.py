"""WJP Rule of Law Index 2025 historical country scores."""
import release_runtime
import io, hashlib, re
import requests
from openpyxl import load_workbook
URL = 'https://worldjusticeproject.org/rule-of-law-index/downloads/2025_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx'
DOC = 'https://worldjusticeproject.org/our-work/research-and-data/wjp-rule-law-index-2021/current-historical-data'

def country(code, year=''):
    if not isinstance(code, str) or not re.fullmatch('[A-Z]{3}', code):
        raise ValueError('Use a three-letter country code')
    if not isinstance(year, str) or (year and (not re.fullmatch('20\\d{2}(?:-20\\d{2})?', year))):
        raise ValueError('Invalid year label')
    with requests.get(URL, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 5000000:
                raise ValueError('Workbook too large')
        modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    s = w['Historical Data']
    it = s.iter_rows(values_only=True)
    headers = list(next(it))
    if len(set(headers)) != len(headers) or headers[:4] != ['Country', 'Year', 'Country_year', 'Country Code']:
        raise ValueError('Unexpected workbook headers')
    rows = []
    for row in it:
        if row[3] != code or (year and str(row[1]) != year):
            continue
        rows.append(dict(zip(headers, row)))
    return {'source': URL, 'methodology': DOC, 'sha256': hashlib.sha256(raw).hexdigest(), 'last_modified_header': modified, 'edition': '2025', 'country_code': code, 'year_filter': year, 'matched': len(rows), 'records': rows, 'notes': ['World Justice Project is an independent research organization; this is a survey- and expert-based index, not official judicial case statistics.', 'Scores range from 0 to 1, with higher representing stronger rule-of-law performance under WJP methodology; country coverage and methods vary.', 'The workbook explicitly states 2015–2018 scores were revised; comparisons over time require caution and scores are not absolute counts.', 'Current downloaded 2025-edition historical file may be updated later; it is not a snapshot of what was published in each historical year.']}
