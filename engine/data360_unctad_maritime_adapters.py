"""UNCTAD container port throughput as hosted by World Bank Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
DATASET = 'UNCTAD_MT'
INDICATOR = 'UNCTAD_MT_CONTAINER_THROUGHPUT'

def container_throughput(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    p = {'DATABASE_ID': DATASET, 'INDICATOR': INDICATOR, 'REF_AREA': country, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', BASE + '?' + urlencode(p)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    if not isinstance(j.get('count'), int) or not isinstance(j.get('value'), list) or j['count'] != len(j['value']) or (len(j['value']) > 1):
        raise ValueError('unexpected data count')
    if any((x.get('DATABASE_ID') != DATASET or x.get('INDICATOR') != INDICATOR or x.get('REF_AREA') != country or (x.get('TIME_PERIOD') != str(year)) or (x.get('UNIT_MEASURE') != 'TEU') or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in j['value'])):
        raise ValueError('response does not match requested series')
    return {'source': 'UNCTAD maritime dataset via World Bank Data360', 'indicator': 'Container port throughput', 'country': country, 'year': year, 'unit': 'TEU (twenty-foot equivalent unit)', 'data': j['value'], 'note': 'Data360 may lag UNCTAD original; values may be revised. Empty data is not zero. Cite UNCTAD Data Hub.'}
