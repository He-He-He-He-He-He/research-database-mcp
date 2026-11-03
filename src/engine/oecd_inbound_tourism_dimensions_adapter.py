"""OECD inbound tourism multidimensional annual observations."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.CFE.TOU,DSD_TOURISM_INTER@DF_INBOUND,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.CFE.TOU&df%5Bid%5D=DSD_TOURISM_INTER%40DF_INBOUND&df%5Bvs%5D=1.0'

def query(country, start, end, measure=''):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    if not isinstance(measure, str) or not re.fullmatch('[A-Z0-9_]{0,40}', measure):
        raise ValueError('invalid measure')
    country = country.upper()
    r = requests.get(BASE + country + '......', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204:
        rows = []
    elif r.status_code == 404 and r.text.strip() == 'NoRecordsFound':
        rows = []
    else:
        r.raise_for_status()
        if len(r.content) > 12000000:
            raise ValueError('response exceeds 12 MB')
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'COUNTERPART_AREA', 'MEASURE', 'UNIT_MEASURE', 'VISITOR_TYPE', 'ACCOMMODATION_TYPE', 'SOURCE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country for x in rows)):
            raise ValueError('unexpected destination')
        if measure:
            rows = [x for x in rows if x['MEASURE'] == measure]
    return {'source': r.url, 'documentation': DOC, 'records': rows, 'note': 'Inbound tourism measures differ by visitor type, origin, accommodation, source and unit. ARRIVALS counts arrivals not unique people; NIGHTS_ACCOM counts nights not visitors. TSS accommodation establishment data differs from border or survey records. Total and component categories overlap: do not add them. Preserve both status fields, unit multipliers and missing values; 404 NoRecordsFound means no observations for this query, not zero.'}
