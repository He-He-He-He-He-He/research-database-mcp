"""World Bank What a Waste 3.0 2026 country/city data and source codebooks."""
import release_runtime
import datetime
import io
import re
import requests
import openpyxl
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0039597/what-a-waste-global-database'
BASE = 'https://datacatalogfiles.worldbank.org/ddh-published/0039597/'
FILES = {'country': BASE + 'DR0095901/What_a_Waste_3.0_COUNTRY_Dataset_%26_Codebook.xlsx', 'city': BASE + 'DR0095900/What_a_Waste_3.0_CITY_Dataset_%26_Codebook.xlsx'}

def _clean(values):
    return [x.isoformat() if isinstance(x, (datetime.datetime, datetime.date)) else x for x in values]

def query(kind, country, mode='data', city='', measurement='', offset=0, limit=20):
    if kind not in FILES or mode not in ('data', 'codebook'):
        raise ValueError('invalid kind or mode')
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be ISO3')
    if city and kind != 'city':
        raise ValueError('city filter requires city data')
    if measurement and mode != 'codebook':
        raise ValueError('measurement filter requires codebook')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    r = requests.get(FILES[kind], timeout=90)
    r.raise_for_status()
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        s = w['Codebook' if mode == 'codebook' else 'Country dataset' if kind == 'country' else 'City dataset']
        it = s.iter_rows(values_only=True)
        first = list(next(it))
        labels = None
        if mode == 'data' and kind == 'country':
            labels = first
            headers = list(next(it))
        else:
            headers = first
        end = max((i for i, x in enumerate(headers) if x is not None), default=-1) + 1
        headers = headers[:end]
        if 'iso3c' not in headers:
            raise ValueError('unexpected source headers')
        iso = headers.index('iso3c')
        ci = headers.index('city_name') if 'city_name' in headers else None
        mi = headers.index('measurement') if 'measurement' in headers else None
        if city and ci is None or (measurement and mi is None):
            raise ValueError('source filter field missing')
        rows = []
        for row in it:
            if str(row[iso] or '').upper() != country.upper():
                continue
            if city and str(row[ci] or '').strip().casefold() != city.strip().casefold():
                continue
            if measurement and str(row[mi] or '').strip().casefold() != measurement.strip().casefold():
                continue
            rows.append(_clean(row[:len(headers)]))
        return {'source': FILES[kind], 'catalog': CATALOG, 'license': 'https://creativecommons.org/licenses/by/4.0/', 'kind': kind, 'mode': mode, 'country': country.upper(), 'download_bytes': len(r.content), 'headers': headers, 'display_labels': labels[:len(headers)] if labels is not None else None, 'total_matches': len(rows), 'offset': offset, 'limit': limit, 'rows': rows[offset:offset + limit], 'notes': ['Rows are positional arrays aligned with headers: duplicate city column names exist and are intentionally not collapsed.', 'Country and city data may be based on different years and sources; reported, modelled, interpolated and projected values must be distinguished using original field labels and codebook.', 'Codebook records carry source, date, units, method and notes where available; some fields may be absent or inconsistent. Empty cells are not zero.', 'Coverage is municipal solid waste according to source definitions, not all waste; country and city figures are not independent samples or safely additive.', 'Fixed March 2026 dataset release; some country codebook date and cited source year can conflict and require checking original references.']}
    finally:
        w.close()
