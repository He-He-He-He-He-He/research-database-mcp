"""World Bank Enterprise Surveys internet disruptions indicator via Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def internet_disruptions(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2021 <= year <= 2100):
        raise ValueError('invalid year')
    dims = {'DATABASE_ID': 'WB_ES', 'INDICATOR': 'WB_ES_T_BREADY_IN21', 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_T', 'COMP_BREAKDOWN_2': '_T', 'COMP_BREAKDOWN_3': '_T'}
    p = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', BASE + '?' + urlencode(p)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(year) or x.get('UNIT_MEASURE') != 'PT' or (x.get('UNIT_MULT') != 0) for x in rows)):
        raise ValueError('response does not match request')
    return {'source': 'World Bank Enterprise Surveys via Data360', 'indicator': 'Firms experiencing internet disruptions', 'country': country, 'survey_year': year, 'unit': 'percent of surveyed firms', 'data': rows, 'note': 'Survey asks about the last completed fiscal year, including downtime and slowdowns but excluding disruptions directly caused by power outages. Sample scope is not all firms. Empty data is not zero.'}
