"""Census American Community Survey metadata and key-protected query."""
import release_runtime
import argparse, json, os, re
import requests
BASE = 'https://api.census.gov/data/'
DISCLAIMER = 'This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.'

def _base(year, series):
    if not isinstance(year, int) or not 2005 <= year <= 2100 or series not in ('acs1', 'acs5'):
        raise ValueError('invalid ACS vintage or series')
    return f'{BASE}{year}/acs/{series}'

def _get(url, params=None):
    with requests.get(url, params=params, timeout=40, stream=True) as r:
        if not r.ok:
            raise ValueError(f'Census service returned HTTP {r.status_code}')
        parts = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 12 * 1024 * 1024:
                raise ValueError('response exceeds 12 MiB')
            parts.append(b)
        try:
            data = json.loads(b''.join(parts))
        except ValueError as e:
            raise ValueError('Census did not return JSON; check key and service status') from e
    return data

def groups(year, series, keyword='', limit=30, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 100000):
        raise ValueError('invalid search')
    url = _base(year, series) + '/groups.json'
    payload = _get(url)
    if not isinstance(payload, dict) or not isinstance(payload.get('groups'), list) or any((not isinstance(x, dict) for x in payload['groups'])):
        raise ValueError('Census group directory is missing or malformed')
    groups = payload['groups']
    found = [x for x in groups if keyword.casefold() in (str(x.get('name', '')) + ' ' + str(x.get('description', ''))).casefold()]
    selected = found[offset:offset + limit]
    return {'source': url, 'total': len(found), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(found) else None, 'truncated': offset + len(selected) < len(found), 'groups': selected, 'disclaimer': DISCLAIMER, 'note': 'Local slice of the full source group list; each request refetches the directory and source ordering may change. Metadata group availability does not imply access to all observations.'}

def group(year, series, code):
    if not re.fullmatch('[A-Za-z0-9_]{1,30}', code):
        raise ValueError('invalid group')
    url = _base(year, series) + '/groups/' + code + '.json'
    return {'source': url, 'data': _get(url), 'disclaimer': DISCLAIMER}

def geographies(year, series):
    url = _base(year, series) + '/geography.json'
    return {'source': url, 'data': _get(url), 'disclaimer': DISCLAIMER}

def query(year, series, variables, geo):
    if not re.fullmatch('[A-Za-z0-9_]+(?:,[A-Za-z0-9_]+){0,24}', variables):
        raise ValueError('invalid variables')
    if not re.fullmatch('(?:us:1|state:[0-9]{2})', geo):
        raise ValueError('geography must be us:1 or state:NN')
    key = release_runtime.environment.get('US_CENSUS_API_KEY', '')
    if not key:
        raise ValueError('Set US_CENSUS_API_KEY; request and activate a personal key from Census Bureau')
    url = _base(year, series)
    try:
        data = _get(url, {'get': variables, 'for': geo, 'key': key})
    except requests.RequestException as e:
        raise RuntimeError('Census request failed; check network and key') from None
    return {'source': url, 'query': {'get': variables, 'for': geo}, 'data': data, 'disclaimer': DISCLAIMER}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    for n in ['groups', 'group', 'geographies', 'query']:
        a = s.add_parser(n)
        a.add_argument('year', type=int)
        a.add_argument('--series', choices=['acs1', 'acs5'], default='acs5')
        if n == 'groups':
            a.add_argument('--keyword', default='')
            a.add_argument('--limit', type=int, default=30)
            a.add_argument('--offset', type=int, default=0)
        if n == 'group':
            a.add_argument('code')
        if n == 'query':
            a.add_argument('variables')
            a.add_argument('geography')
    a = p.parse_args()
    result = groups(a.year, a.series, a.keyword, a.limit, a.offset) if a.cmd == 'groups' else group(a.year, a.series, a.code) if a.cmd == 'group' else geographies(a.year, a.series) if a.cmd == 'geographies' else query(a.year, a.series, a.variables, a.geography)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
