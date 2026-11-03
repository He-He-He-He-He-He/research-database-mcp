"""OECD data-and-voice mobile broadband subscriptions via Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def data_voice(country, year, unit='PER_IH2'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('invalid year')
    if unit not in ('PER_IH2', 'SB'):
        raise ValueError('unit must be PER_IH2 (per 100 inhabitants) or SB (subscriptions)')
    dims = {'DATABASE_ID': 'OECD_BROADBAND', 'INDICATOR': 'OECD_BROADBAND_VD', 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': 'OECD_BROADBAND_INDICATOR_TYPE_MBB', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z', 'UNIT_MEASURE': unit}
    p = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    url = BASE + '?' + urlencode(p)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1):
        raise ValueError('unexpected data count')
    if any((any((x.get(k) != v for k, v in dims.items())) or x.get('TIME_PERIOD') != str(year) or x.get('UNIT_MULT') != 0 or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('response dimensions do not match request')
    return {'source': 'OECD Broadband Database via World Bank Data360', 'source_url': url, 'indicator': 'Mobile broadband data and voice subscriptions', 'country': country, 'year': year, 'unit': 'subscriptions per 100 inhabitants' if unit == 'PER_IH2' else 'subscriptions', 'data': rows, 'note': 'Subscription counts, not unique users; rates can exceed 100. Data360 may lag the OECD source. Verify source reuse terms.'}
