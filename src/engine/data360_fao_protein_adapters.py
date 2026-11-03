"""FAO food supply: animal-origin protein, three-year mean, via Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def animal_protein_supply(country, end_year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(end_year, bool) or not isinstance(end_year, int) or (not 1962 <= end_year <= 2100):
        raise ValueError('invalid year')
    dims = {'DATABASE_ID': 'FAO_FS', 'INDICATOR': 'FAO_FS_21014', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    params = {**dims, 'timePeriodFrom': str(end_year), 'timePeriodTo': str(end_year)}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', BASE + '?' + urlencode(params)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(end_year) or x.get('UNIT_MEASURE') != 'G_PS_D' or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('response dimensions do not match request')
    return {'source': 'FAO Suite of Food Security Indicators via World Bank Data360', 'indicator': 'Average supply of protein of animal origin, three-year average', 'country': country, 'end_year': end_year, 'unit': 'grams per person per day', 'data': rows, 'note': 'Food supply estimate, not direct dietary intake. Verify three-year period in COMMENT_OBS; source data may be updated and reused subject to FAO terms.'}
