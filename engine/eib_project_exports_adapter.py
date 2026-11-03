"""EIB projects pipeline and signed loans: official on-demand XLSX export."""
import release_runtime
import io
import requests
import openpyxl
BASE = 'https://www.eib.org/provider-eib-plr/app/'
SOURCES = {'pipeline': ('pipelines/excel', 'Pipelines'), 'loans': ('loans/excel', 'Loans')}
DOC = 'https://www.eib.org/en/projects/pipelines/notice/index.htm'

def search(kind, country='', keyword='', offset=0, limit=20):
    if kind not in SOURCES:
        raise ValueError('kind must be pipeline or loans')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('limit must be 1 to 500')
    path, sheet_name = SOURCES[kind]
    url = BASE + path
    r = requests.get(url, params={'language': 'en'}, timeout=90)
    r.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        rows = wb[sheet_name].iter_rows(values_only=True)
        headers = list(next(rows))
        if len(headers) != len(set(headers)) or not set(['Sector']).issubset(headers):
            raise ValueError('unexpected export columns')
        col = 'Country' if kind == 'pipeline' else 'Country or Territory'
        if col not in headers:
            raise ValueError('missing country column')
        matches = []
        for values in rows:
            row = dict(zip(headers, values))
            if country and country.casefold().strip() not in str(row[col] or '').casefold():
                continue
            if keyword and keyword.casefold().strip() not in ' '.join((str(v or '') for v in values)).casefold():
                continue
            matches.append(row)
        return {'source': url, 'methodology': DOC, 'kind': kind, 'download_bytes': len(r.content), 'http_last_modified': r.headers.get('Last-Modified'), 'headers': headers, 'total_rows': len(matches), 'offset': offset, 'limit': limit, 'rows': matches[offset:offset + limit], 'notes': ['Official export downloaded and filtered locally; filters use case-insensitive substring matching. No export timestamp is supplied unless HTTP Last-Modified is present.', 'Pipeline export contains historical Signed rows despite the explanatory page saying signed projects normally remain six months; treat actual row status and date as given, not a current pipeline guarantee. Approved does not mean signed or disbursed.', 'Signed loans are finance contracts, not actual disbursement. Signed Amount is preserved as an original formatted currency string; projects and funding instruments may repeat.', 'Only projects covered by disclosure policy are included; non-disclosure is not evidence of no project.']}
    finally:
        wb.close()
