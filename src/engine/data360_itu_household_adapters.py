"""ITU household computer ownership estimates via World Bank Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def computer_households(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('invalid year')
    dims = {'DATABASE_ID': 'ITU_DH', 'INDICATOR': 'IT_HH_COMP', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    params = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    url = BASE + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(year) or x.get('UNIT_MEASURE') != 'PT_HH' or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('response does not match request')
    return {'source': 'ITU DataHub via World Bank Data360', 'indicator': 'Percentage of households with a computer', 'source_url': url, 'country': country, 'year': year, 'unit': 'percent of households', 'data': rows, 'note': 'Computers include desktops, laptops and tablets. Data360 may lag source; empty data is not zero. Check source reuse terms.'}
