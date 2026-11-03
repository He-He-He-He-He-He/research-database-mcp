"""OECD annual resident foreign-born population by country of birth."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.IMD,DSD_MIG_F@DF_MIG_POPF,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.ELS.IMD&df%5Bid%5D=DSD_MIG_F%40DF_MIG_POPF&df%5Bvs%5D=1.0'

def query(destination, birth_country, start, end):
    if not isinstance(destination, str) or not re.fullmatch('[A-Za-z]{3}', destination):
        raise ValueError('destination must be three letters')
    if not isinstance(birth_country, str) or not re.fullmatch('[A-Za-z]{3}', birth_country):
        raise ValueError('birth country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    dest = destination.upper()
    birth = birth_country.upper()
    r = requests.get(BASE + f'{dest}.{birth}.A.._T...', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'BIRTH_COUNTRY', 'FREQ', 'MEASURE', 'SEX', 'BIRTH_PLACE', 'EDUCATION_LEV', 'UNIT_MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': dest, 'BIRTH_COUNTRY': birth, 'FREQ': 'A', 'MEASURE': 'B14', 'SEX': '_T', 'BIRTH_PLACE': '_Z', 'EDUCATION_LEV': '_Z', 'UNIT_MEASURE': 'PS', 'UNIT_MULT': '0'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'destination': dest, 'birth_country': birth, 'records': rows, 'note': 'Annual resident stock of population born in specified country, persons. Birth country is not citizenship; stock is not annual inflow. National definitions and methods are not fully comparable and may include rounding; year-on-year change is not migration flow. Preserve original status and nulls; no rows does not mean zero.'}
