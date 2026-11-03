"""ABS SDMX established-house transfers, quarterly, Greater Sydney or rest of NSW."""
import release_runtime
import csv
import io
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.api.abs.gov.au/rest/data/ABS,RES_DWELL/'
REGIONS = {'1GSYD': 'Greater Sydney', '1RNSW': 'Rest of New South Wales'}

def established_house_transfers(region, start, end):
    if region not in REGIONS:
        raise ValueError('region must be 1GSYD or 1RNSW')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('\\d{4}-Q[1-4]', start)) or (not re.fullmatch('\\d{4}-Q[1-4]', end)):
        raise ValueError('period must be YYYY-Q1 through YYYY-Q4')

    def q(x):
        return int(x[:4]) * 4 + int(x[-1])
    if q(start) > q(end) or q(end) - q(start) > 39:
        raise ValueError('period range must be ordered and at most 40 quarters')
    url = BASE + '1.' + region + '.Q?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', url], capture_output=True, text=True, check=True)
    reader = csv.DictReader(io.StringIO(r.stdout))
    fields = {'DATAFLOW', 'MEASURE', 'REGION', 'FREQ', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE', 'UNIT_MULT', 'OBS_STATUS', 'OBS_COMMENT'}
    if not reader.fieldnames or not fields.issubset(reader.fieldnames):
        raise ValueError('unexpected ABS CSV')
    rows = list(reader)
    if any((not x['DATAFLOW'].startswith('ABS:RES_DWELL(') or x['MEASURE'] != '1' or x['REGION'] != region or (x['FREQ'] != 'Q') or (x['UNIT_MEASURE'] != 'NUM') or (x['UNIT_MULT'] != '0') or (not re.fullmatch('\\d{4}-Q[1-4]', x['TIME_PERIOD'])) or (not q(start) <= q(x['TIME_PERIOD']) <= q(end)) for x in rows)):
        raise ValueError('response does not match request')
    return {'source': 'Australian Bureau of Statistics', 'series': 'number of established house transfers', 'region': REGIONS[region], 'frequency': 'quarterly', 'unit': 'number of transfers', 'rows': rows, 'note': 'Official values may be revised; status and comments are preserved.'}
