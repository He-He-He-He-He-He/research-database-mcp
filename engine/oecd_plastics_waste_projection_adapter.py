"""OECD baseline plastic waste projections by model region and fate."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ENV.EEI,DSD_PW_P@DF_PW_P,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.ENV.EEI&df%5Bid%5D=DSD_PW_P%40DF_PW_P&df%5Bvs%5D=1.0'

def query(region, start, end):
    if not isinstance(region, str) or not re.fullmatch('[A-Za-z0-9_]{2,20}', region):
        raise ValueError('invalid OECD model-region code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    region = region.upper()
    r = requests.get(BASE + region + '..A..', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() == 'NoRecordsFound'):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'MEASURE', 'FREQ', 'PLASTIC_END_LIFE', 'SCENARIO', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT', 'UNIT_MEASURE'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': region, 'MEASURE': 'PW_EL_REGION_PROJECTION', 'FREQ': 'A', 'SCENARIO': 'CENTRAL_BASELINE', 'UNIT_MULT': '6', 'UNIT_MEASURE': 'T'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions or units')
    return {'source': r.url, 'documentation': DOC, 'region': region, 'records': rows, 'note': 'OECD ENV-Linkages baseline scenario model projections, not measured waste or a certain forecast. Values are in millions of tonnes (source UNIT_MEASURE=T and UNIT_MULT=6); raw OBS_VALUE is unchanged. Regions are model groupings, not necessarily countries. TOTAL overlaps recycled, incinerated, landfilled and mismanaged categories; do not add total to components. Preserve status and missing values.'}
