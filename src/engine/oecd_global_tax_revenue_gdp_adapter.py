"""OECD Global Revenue Statistics general government taxes as % of GDP."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,2.1/'
CATEGORIES = {'total': '_T', 'income': 'T_1000', 'social': 'T_2000', 'payroll': 'T_3000', 'property': 'T_4000', 'goods': 'T_5000', 'other': 'T_6000'}
DOC = 'https://www.oecd.org/en/data/datasets/global-revenue-statistics-database.html'

def query(country, category, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if category not in CATEGORIES:
        raise ValueError('invalid category')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    country = country.upper()
    cat = CATEGORIES[category]
    u = BASE + f'{country}..S13.{cat}..PT_B1GQ.A'
    r = requests.get(u, params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        expected = {'REF_AREA', 'MEASURE', 'SECTOR', 'STANDARD_REVENUE', 'CTRY_SPECIFIC_REVENUE', 'UNIT_MEASURE', 'FREQ', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not expected.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': country, 'MEASURE': 'TAX_REV', 'SECTOR': 'S13', 'STANDARD_REVENUE': cat, 'CTRY_SPECIFIC_REVENUE': '_T', 'UNIT_MEASURE': 'PT_B1GQ', 'FREQ': 'A', 'UNIT_MULT': '0'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'catalog': DOC, 'category': category, 'records': rows, 'note': 'OECD harmonized general government tax revenue as % of GDP, including compulsory social security contributions where classified as tax. Category 1000 is income/profits/capital gains, not total tax. The total includes components and must not be added to them; values may be preliminary or estimated according to OBS_STATUS. Null/empty results are not zero. Fiscal year and GDP reference may differ across countries; consult OECD country notes.'}
