"""ILOSTAT annual average weekly hours actually worked for total sex and age 15+, read-only."""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://sdmx.ilo.org/rest'
FLOW = 'DF_HOW_TEMP_SEX_AGE_NB'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--write-out', '\n%{http_code}', BASE + path], capture_output=True, text=True, check=True)
    body, status = r.stdout.rsplit('\n', 1)
    return None if status == '204' else body

def metadata():
    body = _get('/dataflow/ILO/' + FLOW + '/latest')
    if body is None:
        raise ValueError('missing dataflow')
    root = ET.fromstring(body)
    matches = [x for x in root.iter() if x.tag.endswith('}Dataflow') and x.get('id') == FLOW]
    if len(matches) != 1:
        raise ValueError('unexpected dataflow')
    names = [x.text for x in matches[0] if x.tag.endswith('}Name') and x.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en']
    if not names:
        raise ValueError('missing label')
    return {'code': FLOW, 'name': names[0], 'version': matches[0].get('version')}

def hours(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be three uppercase letters')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    path = '/data/ILO,' + FLOW + '/' + country + '.A..SEX_T.AGE_YTHADULT_YGE15?' + urlencode({'startPeriod': year, 'endPeriod': year, 'format': 'csv'})
    body = _get(path)
    if body is None:
        return []
    reader = csv.DictReader(io.StringIO(body))
    if not reader.fieldnames or not {'REF_AREA', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE', 'UNIT_MULT'}.issubset(reader.fieldnames):
        raise ValueError('unexpected ILOSTAT CSV')
    records = list(reader)
    if any((x['REF_AREA'] != country or x['TIME_PERIOD'] != str(year) or x['SEX'] != 'SEX_T' or (x['AGE'] != 'AGE_YTHADULT_YGE15') for x in records)):
        raise ValueError('unexpected series')
    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('metadata')
    q = sub.add_parser('data')
    q.add_argument('country')
    q.add_argument('year', type=int)
    a = parser.parse_args()
    print(json.dumps(metadata() if a.command == 'metadata' else hours(a.country, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
