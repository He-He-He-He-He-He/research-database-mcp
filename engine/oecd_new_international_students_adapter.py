"""OECD standardized temporary-migration inflow for new international students."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.IMD,DSD_MIG_INT@DF_MIG_INT_TEMP,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.ELS.IMD&df%5Bid%5D=DSD_MIG_INT%40DF_MIG_INT_TEMP&df%5Bvs%5D=1.0'

def query(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    country = country.upper()
    r = requests.get(BASE + f'{country}.A..STU.', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'FREQ', 'MEASURE', 'MIGRATION_TYPE', 'UNIT_MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': country, 'FREQ': 'A', 'MEASURE': 'MIG_FLW', 'MIGRATION_TYPE': 'STU', 'UNIT_MEASURE': 'PS', 'UNIT_MULT': '0'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'country': country, 'records': rows, 'note': 'Annual standardized inflow of international students newly registered in tertiary education, persons, as defined by OECD temporary migration series. It is not the stock of international students enrolled, all arrivals, or an estimate of students from a particular origin. Country definitions and coverage may vary; preserve statuses and do not treat missing as zero.'}
