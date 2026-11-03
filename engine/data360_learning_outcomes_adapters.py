"""World Bank Harmonized Learning Outcomes results via Data360."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATORS = {'score': 'WB_HLO_SCORE', 'standard_error': 'WB_HLO_SCORE_SE'}

def learning_outcomes(country, year, measure='score'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('invalid year')
    if measure not in INDICATORS:
        raise ValueError('measure must be score or standard_error')
    indicator = INDICATORS[measure]
    p = {'DATABASE_ID': 'WB_HLO', 'INDICATOR': indicator, 'REF_AREA': country, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', BASE + '?' + urlencode(p)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    rows = j.get('value')
    expected = 'SCORE' if measure == 'score' else 'STD_ERR'
    if not isinstance(j.get('count'), int) or not isinstance(rows, list) or j['count'] != len(rows) or (len(rows) > 1000):
        raise ValueError('incomplete or unexpected result')
    if any((x.get('DATABASE_ID') != 'WB_HLO' or x.get('INDICATOR') != indicator or x.get('REF_AREA') != country or (x.get('TIME_PERIOD') != str(year)) or (x.get('UNIT_MEASURE') != expected) or (x.get('UNIT_MULT') != 0) for x in rows)):
        raise ValueError('response dimensions do not match request')
    return {'source': 'World Bank Harmonized Learning Outcomes via Data360', 'country': country, 'year': year, 'measure': measure, 'data': rows, 'note': 'Scores are harmonized across assessments, not raw PISA scores. Preserve sex, subject, grade, test and national-representativeness comments. Empty data is not zero.'}
