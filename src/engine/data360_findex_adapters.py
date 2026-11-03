"""World Bank Global Findex: account ownership, 15+ respondents, Data360 API."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
DATASET = 'WB_FINDEX'
INDICATOR = 'WB_FINDEX_ACCOUNT_T_D'

def account_ownership(country, year, sex='_T'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2011 <= year <= 2100):
        raise ValueError('invalid year')
    if sex not in ('_T', 'M', 'F'):
        raise ValueError('sex must be _T, M, or F')
    dims = {'DATABASE_ID': DATASET, 'INDICATOR': INDICATOR, 'REF_AREA': country, 'SEX': sex, 'AGE': 'Y_GE15', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_T', 'COMP_BREAKDOWN_2': '_T', 'COMP_BREAKDOWN_3': '_T'}
    p = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', BASE + '?' + urlencode(p)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(year) or x.get('UNIT_MEASURE') != 'PT_RESP' or (x.get('UNIT_MULT') != 0) for x in rows)):
        raise ValueError('response does not match requested series')
    return {'source': 'World Bank Global Findex via Data360', 'indicator': 'Account ownership', 'country': country, 'year': year, 'sex': sex, 'unit': 'percent of respondents aged 15+', 'data': rows, 'note': 'Survey estimate: respondents reporting a financial institution account or personal mobile money use in the preceding 12 months. Empty data is not zero.'}
