"""FAO food supply: cereals, roots and tubers energy share, three-year mean, via Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def staple_energy_share(country, end_year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(end_year, bool) or not isinstance(end_year, int) or (not 1962 <= end_year <= 2100):
        raise ValueError('invalid year')
    dims = {'DATABASE_ID': 'FAO_FS', 'INDICATOR': 'FAO_FS_21012', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    params = {**dims, 'timePeriodFrom': str(end_year), 'timePeriodTo': str(end_year)}
    url = BASE + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(end_year) or x.get('UNIT_MEASURE') != 'PT' or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('response dimensions do not match request')
    return {'source': 'FAO Suite of Food Security Indicators via World Bank Data360', 'source_url': url, 'indicator': 'Share of dietary energy supply from cereals, roots and tubers, three-year average', 'country': country, 'end_year': end_year, 'unit': 'percent of total dietary energy supply', 'data': rows, 'note': 'Food energy supply share, not individual consumption or dietary sufficiency. Verify three-year period in COMMENT_OBS; FAO source data may be revised.'}
