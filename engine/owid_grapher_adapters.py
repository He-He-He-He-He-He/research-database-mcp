"""Read OWID chart metadata and filter public chart CSV by country and year."""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
import threading
import time
BASE = 'https://ourworldindata.org/grapher/'
_lock = threading.Lock()
_last = 0.0

def _get(slug, suffix):
    global _last
    if not isinstance(slug, str) or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', slug) or len(slug) > 100:
        raise ValueError('invalid chart slug')
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + slug + suffix], capture_output=True, text=True, check=True)
    return r.stdout

def chart_metadata(slug):
    result = json.loads(_get(slug, '.metadata.json'))
    if not isinstance(result, dict) or not isinstance(result.get('columns'), dict):
        raise ValueError('unexpected metadata')
    return result

def observations(slug, country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9_]{3,20}', country):
        raise ValueError('invalid entity code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1700 <= year <= 2100):
        raise ValueError('invalid year')
    csvtext = _get(slug, '.csv')
    reader = csv.DictReader(io.StringIO(csvtext))
    if not reader.fieldnames or not {'Code', 'Year'}.issubset(reader.fieldnames):
        raise ValueError('chart lacks Code or Year')
    return [r for r in reader if r.get('Code') == country and r.get('Year') == str(year)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    a = sub.add_parser('metadata')
    a.add_argument('slug')
    b = sub.add_parser('data')
    b.add_argument('slug')
    b.add_argument('country')
    b.add_argument('year', type=int)
    args = parser.parse_args()
    result = chart_metadata(args.slug) if args.command == 'metadata' else observations(args.slug, args.country, args.year)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
