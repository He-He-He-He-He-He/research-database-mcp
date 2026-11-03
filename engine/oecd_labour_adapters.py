"""OECD annual labour-force participation, age 15–64, with labelled dimensions."""
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
BASE = 'https://sdmx.oecd.org/public/rest/v1/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_LF_WAP_Q,1.0/'
_lock = threading.Lock()
_last_request = 0.0

def labour_participation(country, year):
    """Fetch annual rate for one OECD reference area and year, all sexes."""
    global _last_request
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase reference-area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('year must be between 1950 and 2100')
    url = BASE + country + '.LF_WAP.._Z.Y._T.Y15T64..A?' + urlencode({'startPeriod': year, 'endPeriod': year})
    with _lock:
        delay = 1.0 - (time.monotonic() - _last_request)
        if delay > 0:
            time.sleep(delay)
        _last_request = time.monotonic()
        result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--header', 'Accept: application/vnd.sdmx.data+csv;version=2.0.0;labels=both', url], capture_output=True, text=True, check=True)
    reader = csv.DictReader(io.StringIO(result.stdout))
    if not reader.fieldnames or 'OBS_VALUE: Observation value' not in reader.fieldnames:
        raise ValueError('unexpected OECD CSV response')
    return list(reader)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('country')
    parser.add_argument('year', type=int)
    args = parser.parse_args()
    print(json.dumps(labour_participation(args.country, args.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
