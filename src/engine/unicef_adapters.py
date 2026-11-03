"""Fetch a bounded UNICEF cross-sector indicator SDMX-JSON series."""
import release_runtime
import argparse
import json
import re
import subprocess
import time
BASE = 'https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/'
_last_request = 0.0

def query_indicator(country, indicator, sex='_T'):
    global _last_request
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase code')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9_]{1,80}', indicator):
        raise ValueError('invalid indicator code')
    if not isinstance(sex, str) or not re.fullmatch('[A-Z0-9_]{1,20}', sex):
        raise ValueError('invalid sex code')
    delay = 1.0 - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    _last_request = time.monotonic()
    url = BASE + country + '.' + indicator + '.' + sex + '?format=sdmx-json'
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if not isinstance(data, dict) or not isinstance(data.get('data', {}).get('structure'), dict) or (not isinstance(data['data'].get('dataSets'), list)):
        raise ValueError('unexpected UNICEF SDMX response')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('country')
    parser.add_argument('indicator')
    parser.add_argument('--sex', default='_T')
    args = parser.parse_args()
    print(json.dumps(query_indicator(args.country, args.indicator, args.sex), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
