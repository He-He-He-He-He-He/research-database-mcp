"""Read ECB euro-area HICP monthly annual-change data with original metadata."""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://data-api.ecb.europa.eu/service/data/HICP/M.U2.N.000000.4D0.ANR'
_lock = threading.Lock()
_last = 0.0

def inflation_month(month):
    global _last
    if not isinstance(month, str) or not re.fullmatch('(?:19|20)[0-9]{2}-(?:0[1-9]|1[0-2])', month):
        raise ValueError('month must have format YYYY-MM')
    url = BASE + '?' + urlencode({'startPeriod': month, 'endPeriod': month})
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--header', 'Accept: text/csv', '--write-out', '\n%{http_code}', url], capture_output=True, text=True, check=True)
    body, status = r.stdout.rsplit('\n', 1)
    if status == '204':
        return []
    reader = csv.DictReader(io.StringIO(body))
    if not reader.fieldnames or not {'KEY', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT'}.issubset(reader.fieldnames):
        raise ValueError('unexpected ECB response')
    data = list(reader)
    if any((x['KEY'] != 'HICP.M.U2.N.000000.4D0.ANR' or x['TIME_PERIOD'] != month for x in data)):
        raise ValueError('unexpected series or period')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('month')
    args = parser.parse_args()
    print(json.dumps(inflation_month(args.month), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
