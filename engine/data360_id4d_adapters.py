"""World Bank ID4D foundational ID ownership survey estimates via Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def id_ownership(country, year, sex='_T'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2017 <= year <= 2100):
        raise ValueError('invalid year')
    if sex not in ('_T', 'M', 'F'):
        raise ValueError('sex must be _T, M, or F')
    dims = {'DATABASE_ID': 'WB_ID4D', 'INDICATOR': 'ID_OWN', 'REF_AREA': country, 'SEX': sex, 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_T', 'COMP_BREAKDOWN_2': '_T', 'COMP_BREAKDOWN_3': '_T'}
    params = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', BASE + '?' + urlencode(params)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(year) or x.get('UNIT_MEASURE') != 'PT_RESP_SUB' or (x.get('UNIT_MULT') != 0) for x in rows)):
        raise ValueError('response dimensions do not match request')
    return {'source': 'World Bank ID4D Global Dataset via Data360', 'indicator': 'Primary foundational ID ownership', 'country': country, 'year': year, 'sex': sex, 'unit': 'percentage of eligible respondents', 'data': rows, 'note': 'Survey estimate. If the minimum ID age exceeds 15, younger respondents are excluded; empty data is not zero.'}
