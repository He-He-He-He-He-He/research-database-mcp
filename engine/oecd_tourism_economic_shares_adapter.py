"""OECD tourism direct GDP, GVA and employment shares."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.CFE.TOU,DSD_TOURISM_KEY@DF_KEY_IND_PC,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.CFE.TOU&df%5Bid%5D=DSD_TOURISM_KEY%40DF_KEY_IND_PC&df%5Bvs%5D=1.0'
EXPECTED = {'GDP_SH': 'PT_B1GQ', 'GVA_SH': 'PT_B1G', 'EMP_SH': 'PT_EMP'}

def query(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    country = country.upper()
    r = requests.get(BASE + country + '..', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() == 'NoRecordsFound'):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'MEASURE', 'UNIT_MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['MEASURE'] not in EXPECTED or x['UNIT_MEASURE'] != EXPECTED[x['MEASURE']] or (x['UNIT_MULT'] != '0') for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'country': country, 'records': rows, 'note': 'Percent shares of direct tourism GDP, gross value added, and employment use different denominators; do not add or equate them. Direct effects exclude indirect tourism effects. Country tourism satellite-account methodology and update years may differ; retain official observation statuses and blank values. No records do not imply zero.'}
