"""Singapore Department of Statistics Table Builder catalog and bounded series."""
import release_runtime
import argparse, json, re
import requests
ROOT = 'https://tablebuilder.singstat.gov.sg/api/table/'

def _get(path, params):
    with requests.get(ROOT + path, params=params, timeout=40, stream=True, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for c in r.iter_content(65536):
            n += len(c)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        d = json.loads(b''.join(parts))
        if d.get('StatusCode') not in (None, 0, 200):
            raise ValueError('SingStat error: ' + str(d.get('Message'))[:200])
        return {'source': r.url, 'data': d.get('Data')}

def search(keyword, limit=20):
    if not keyword or len(keyword) > 100 or (not 1 <= limit <= 100):
        raise ValueError('invalid search')
    d = _get('resourceid', {'keyword': keyword, 'searchOption': 'all'})
    data = d['data']
    if not isinstance(data, dict) or not isinstance(data.get('records'), list):
        raise ValueError('unexpected catalog')
    return {'source': d['source'], 'total': data.get('total'), 'records': data['records'][:limit], 'note': 'Only first limit records of server search returned.'}

def series(table, row, year):
    if not re.fullmatch('[A-Z]\\d{6}', table) or not isinstance(row, int) or row < 1 or (not 1800 <= year <= 2100):
        raise ValueError('invalid table ID, row or year')
    d = _get('tabledata/' + table, {'seriesNoORrowNo': row, 'timeFilter': str(year)})
    if not isinstance(d['data'], dict) or not isinstance(d['data'].get('row'), list):
        raise ValueError('unexpected table response')
    return d

def rows(table, year, limit=20, offset=0):
    if not re.fullmatch('[A-Z]\\d{6}', table) or not 1800 <= year <= 2100 or (not 1 <= limit <= 100) or (not 0 <= offset <= 10000):
        raise ValueError('invalid table, year or paging')
    d = _get('tabledata/' + table, {'timeFilter': str(year), 'limit': limit, 'offset': offset})
    if not isinstance(d['data'], dict) or not isinstance(d['data'].get('row'), list):
        raise ValueError('unexpected table response')
    return d

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('series')
    a.add_argument('table')
    a.add_argument('row', type=int)
    a.add_argument('year', type=int)
    a = s.add_parser('rows')
    a.add_argument('table')
    a.add_argument('year', type=int)
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    d = search(a.keyword, a.limit) if a.cmd == 'search' else series(a.table, a.row, a.year) if a.cmd == 'series' else rows(a.table, a.year, a.limit, a.offset)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
