"""UNESCO DataHub UIS SDG 4 dataset metadata and bounded records."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/uis001'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path], capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    if not isinstance(data, dict):
        raise ValueError('unexpected UNESCO response')
    return data

def dataset_metadata():
    data = _get('')
    if data.get('dataset_id') != 'uis001' or not isinstance(data.get('fields'), list):
        raise ValueError('unexpected dataset metadata')
    return data

def query_records(indicator, country, limit=25, offset=0):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9_.-]{1,100}', indicator):
        raise ValueError('invalid indicator ID')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('invalid country code')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 9900):
        raise ValueError('offset must be 0–9900')
    where = 'indicator_id="' + indicator + '" AND country_id="' + country + '"'
    path = '/records?' + urlencode({'where': where, 'limit': limit, 'offset': offset})
    data = _get(path)
    if not isinstance(data.get('results'), list):
        raise ValueError('missing records')
    if any((x.get('indicator_id') != indicator or x.get('country_id') != country for x in data['results'])):
        raise ValueError('unexpected record identity')
    return {**data, 'toolkit_source_url': BASE + path, 'toolkit_note': 'Results preserve source values and footnotes. No explicit stable ordering is requested; source changes may produce overlaps or omissions across pages. Verify indicator definitions and units from source metadata.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('metadata')
    q = sub.add_parser('records')
    q.add_argument('indicator')
    q.add_argument('country')
    q.add_argument('--limit', type=int, default=25)
    q.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()
    result = dataset_metadata() if args.command == 'metadata' else query_records(args.indicator, args.country, args.limit, args.offset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
