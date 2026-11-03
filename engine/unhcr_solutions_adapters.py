"""UNHCR Refugee Population Statistics API: bounded durable solutions query."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
from unhcr_population_adapter import _resolve
BASE = 'https://api.unhcr.org/population/v1/solutions/'

def solutions(origin, year_from, year_to, page=1, limit=20, code_system='unhcr'):
    if not isinstance(origin, str) or not re.fullmatch('[A-Z]{3}', origin):
        raise ValueError('origin must be a three-letter uppercase country code')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (year_from, year_to, page, limit))):
        raise ValueError('years, page and limit must be integers')
    if not 1950 <= year_from <= year_to <= 2100:
        raise ValueError('invalid year range')
    if not 1 <= page <= 100 or not 1 <= limit <= 100:
        raise ValueError('page and limit must be 1–100')
    if code_system not in ('unhcr', 'iso3'):
        raise ValueError('code_system must be unhcr or iso3')
    origin_code = _resolve(origin, code_system)
    params = {'coo': origin_code, 'yearFrom': year_from, 'yearTo': year_to, 'page': page, 'limit': limit}
    url = BASE + '?' + urlencode(params)
    response = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    result = json.loads(response.stdout)
    if not isinstance(result, dict) or not isinstance(result.get('items'), list) or result.get('page') != page:
        raise ValueError('unexpected UNHCR response')
    for row in result['items']:
        if row.get('coo') != origin_code or not year_from <= row.get('year', 0) <= year_to:
            raise ValueError('result does not match requested origin or years')
    return {'source': 'UNHCR Refugee Population Statistics Database', 'source_url': url, 'query': params, 'page': result['page'], 'maxPages': result.get('maxPages'), 'total': result.get('total'), 'items': result['items'], 'terms': 'https://www.unhcr.org/terms-use-datasets', 'methodology': 'https://www.unhcr.org/refugee-statistics/methodology/', 'note': 'Source total is an aggregate of solution categories, not record count. Preserve source hyphen/missing markers and do not turn them into zero; disaggregations may overlap. Cross-page results may change when the database updates.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('origin')
    p.add_argument('year_from', type=int)
    p.add_argument('year_to', type=int)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--code-system', choices=['unhcr', 'iso3'], default='unhcr')
    args = p.parse_args()
    print(json.dumps(solutions(args.origin, args.year_from, args.year_to, args.page, args.limit, args.code_system), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
