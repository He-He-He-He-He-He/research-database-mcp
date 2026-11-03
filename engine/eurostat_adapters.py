"""Eurostat bounded JSON-stat dataset query, with dimensions and status preserved."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
MAX_BYTES = 10000000

def query_dataset(dataset, geo, year, filters=None):
    if not isinstance(dataset, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', dataset):
        raise ValueError('invalid dataset code')
    if not isinstance(geo, str) or not re.fullmatch('[A-Za-z0-9_]{1,30}', geo):
        raise ValueError('invalid geography code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('year must be 1900–2100')
    params = {'geo': geo, 'time': str(year), 'lang': 'en'}
    if filters is not None:
        if not isinstance(filters, dict) or len(filters) > 12:
            raise ValueError('filters must be a dictionary with at most 12 entries')
        for key, value in filters.items():
            if not isinstance(key, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,40}', key) or key.lower() in {'geo', 'time', 'lang'}:
                raise ValueError('invalid or reserved dimension name')
            if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', value):
                raise ValueError('invalid dimension value')
            params[key] = value
    url = BASE + dataset + '?' + urlencode(params)
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=30, check=True)
    if len(result.stdout) > MAX_BYTES:
        raise ValueError('Eurostat response exceeds 10 MB; specify more dimension filters')
    data = json.loads(result.stdout)
    if not isinstance(data, dict) or not isinstance(data.get('dimension'), dict) or (not isinstance(data.get('value'), (dict, list))):
        raise ValueError('unexpected Eurostat JSON-stat response')
    for dim, expected in [('geo', geo), ('time', str(year)), *((key, value) for key, value in (filters or {}).items())]:
        entry = data['dimension'].get(dim)
        if not isinstance(entry, dict):
            raise ValueError('Eurostat response omitted requested dimension: ' + dim)
        indices = entry.get('category', {}).get('index', {})
        if isinstance(indices, (dict, list)) and (not indices):
            raise ValueError('Eurostat returned no category for ' + dim + '; code may be invalid or unavailable for this selection')
        if isinstance(indices, (dict, list)) and expected not in indices:
            raise ValueError('Eurostat response does not match requested ' + dim)
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('geo')
    parser.add_argument('year', type=int)
    parser.add_argument('--filter', action='append', default=[], metavar='DIMENSION=CODE')
    args = parser.parse_args()
    filters = {}
    for item in args.filter:
        key, sep, value = item.partition('=')
        if not sep or key in filters:
            parser.error('filters must be unique DIMENSION=CODE entries')
        filters[key] = value
    print(json.dumps(query_dataset(args.dataset, args.geo, args.year, filters), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
