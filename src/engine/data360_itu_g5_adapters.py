"""ITU G5 digital policy benchmarks via the World Bank Data360 API."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATORS = {'overall': 'ITU_ICT_G5_OVRL_SCR', 'digital_economy_policy': 'ITU_ICT_G5_DIG_ECON'}

def benchmark(country, year, indicator='overall'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('invalid year')
    if indicator not in INDICATORS:
        raise ValueError('indicator must be overall or digital_economy_policy')
    dims = {'DATABASE_ID': 'ITU_ICT', 'INDICATOR': INDICATORS[indicator], 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    params = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    url = BASE + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(year) or x.get('UNIT_MEASURE') != '0_TO_100' or (x.get('UNIT_MULT') != 0) for x in rows)):
        raise ValueError('response dimensions do not match request')
    return {'source': 'ITU G5 Benchmark via World Bank Data360', 'source_url': url, 'country': country, 'year': year, 'indicator': indicator, 'data': rows, 'note': 'G5 assesses policy and regulatory frameworks, not 5G or digital economic performance. A pillar score is a contribution to the overall benchmark, not an independently scaled 0–100 score. Check source methodology and reuse terms.'}
