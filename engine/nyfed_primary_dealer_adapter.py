"""NY Fed weekly primary dealer statistics: browse series and obtain observations."""
import release_runtime
import argparse, datetime, json, re, requests
BASE = 'https://markets.newyorkfed.org/api/pd/'

def _read(path):
    r = requests.get(BASE + path, timeout=50)
    r.raise_for_status()
    j = r.json()
    a = j.get('pd', {}).get('timeseries')
    if not isinstance(a, list):
        raise ValueError('unexpected primary dealer response')
    return (a, r.url)

def catalog(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 100 or (not 1 <= limit <= 1000):
        raise ValueError('invalid search')
    a, u = _read('list/timeseries.json')
    a = [x for x in a if keyword.casefold() in (str(x.get('description', '')) + ' ' + str(x.get('keyid', ''))).casefold()]
    return {'source': u, 'matched_count': len(a), 'records': a[:limit]}

def observations(seriesbreak, keyid, start, end, limit=1000):
    if not re.fullmatch('SBN\\d{4}', seriesbreak) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', keyid):
        raise ValueError('invalid series identifier')
    try:
        a, b = (datetime.date.fromisoformat(start), datetime.date.fromisoformat(end))
        if a.isoformat() != start or b.isoformat() != end or a > b or (not 1 <= limit <= 1000):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('invalid dates or limit')
    rows, u = _read('get/' + seriesbreak + '/timeseries/' + keyid + '.json')
    rows = [x for x in rows if start <= x.get('asofdate', '') <= end]
    return {'provider': 'Federal Reserve Bank of New York', 'source': u, 'seriesbreak': seriesbreak, 'keyid': keyid, 'matched_count': len(rows), 'records': rows[:limit], 'note': 'Confirm units and definitions for each series in official release and guidesheets.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('--keyword', default='')
    c.add_argument('--limit', type=int, default=100)
    q = s.add_parser('data')
    q.add_argument('seriesbreak')
    q.add_argument('keyid')
    q.add_argument('start')
    q.add_argument('end')
    q.add_argument('--limit', type=int, default=1000)
    a = p.parse_args()
    v = catalog(a.keyword, a.limit) if a.cmd == 'catalog' else observations(a.seriesbreak, a.keyid, a.start, a.end, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
