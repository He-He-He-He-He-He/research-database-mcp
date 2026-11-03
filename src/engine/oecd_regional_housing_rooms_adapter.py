"""OECD regional housing rooms per inhabitant."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_SOC@DF_HOUSING,2.2/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.CFE.EDS&df%5Bid%5D=DSD_REG_SOC%40DF_HOUSING&df%5Bvs%5D=2.2'

def query(region, start, end):
    if not isinstance(region, str) or not re.fullmatch('[A-Za-z0-9_]{2,15}', region):
        raise ValueError('invalid OECD area code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    region = region.upper()
    r = requests.get(BASE + f'A..{region}..ROOMS...', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() in ('NoRecordsFound', 'NoResultsFound')):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'COUNTRY', 'TERRITORIAL_LEVEL', 'MEASURE', 'UNIT_MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': region, 'MEASURE': 'ROOMS', 'UNIT_MEASURE': 'RO_PS', 'UNIT_MULT': '0'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'region': region, 'records': rows, 'note': 'Rooms per person, not floor space or housing affordability. OECD territorial levels identify country/region and are not interchangeable; retain territorial level, parent country, year and status. Series can be historical, sparse, rounded or have breaks; empty results are not zero and year-on-year equality does not prove no change.'}
