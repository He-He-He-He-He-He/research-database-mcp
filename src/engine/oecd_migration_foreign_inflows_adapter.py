"""OECD international migration annual inflows of foreign population."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.IMD,DSD_MIG@DF_MIG,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.ELS.IMD&df%5Bid%5D=DSD_MIG%40DF_MIG&df%5Bvs%5D=1.0'

def query(destination, citizenship, start, end):
    if not isinstance(destination, str) or not re.fullmatch('[A-Za-z]{3}', destination):
        raise ValueError('destination must be three letters')
    if not isinstance(citizenship, str) or not re.fullmatch('(?:[A-Za-z]{3}|W)', citizenship):
        raise ValueError('citizenship must be three letters or W for world')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    dest = destination.upper()
    cit = citizenship.upper()
    u = BASE + f'{dest}.{cit}.A.B11._T...'
    r = requests.get(u, params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'CITIZENSHIP', 'FREQ', 'MEASURE', 'SEX', 'BIRTH_PLACE', 'EDUCATION_LEV', 'UNIT_MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': dest, 'CITIZENSHIP': cit, 'FREQ': 'A', 'MEASURE': 'B11', 'SEX': '_T', 'BIRTH_PLACE': '_Z', 'EDUCATION_LEV': '_Z', 'UNIT_MEASURE': 'PS', 'UNIT_MULT': '0'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'destination': dest, 'citizenship': cit, 'records': rows, 'note': 'Annual inflows of foreign population in persons, classified by citizenship, not country of birth or total foreign-born resident stock. W is all foreign citizenships; it overlaps individual citizenship series and must not be added to them. National concepts and sources are not fully comparable across countries. Preserve OBS_STATUS and missing values; no rows do not mean zero.'}
