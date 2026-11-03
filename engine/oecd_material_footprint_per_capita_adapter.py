"""OECD material footprint per person, total materials."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_MATERIAL_RESOURCES@DF_MATERIAL_RESOURCES,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.ENV.EPI&df%5Bid%5D=DSD_MATERIAL_RESOURCES%40DF_MATERIAL_RESOURCES&df%5Bvs%5D=1.0'

def query(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    country = country.upper()
    r = requests.get(BASE + country + '.A.MF.T_PS.TOT', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() == 'NoRecordsFound'):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'FREQ', 'MEASURE', 'UNIT_MEASURE', 'GROUP', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': country, 'FREQ': 'A', 'MEASURE': 'MF', 'UNIT_MEASURE': 'T_PS', 'GROUP': 'TOT', 'UNIT_MULT': '0'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'country': country, 'records': rows, 'note': 'Material footprint per person is tonnes per person attributed to domestic final demand, including upstream material extraction globally, not simply domestic extraction or physical waste. OECD derives material footprint series from UNEP global material flows; do not treat the two as independent evidence. Preserve statuses and missing values. Cross-country methods and time revisions may differ.'}
