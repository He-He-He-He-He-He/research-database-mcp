"""Federal Reserve System Open Market Account domestic holdings."""
import release_runtime
import argparse, datetime, json, requests
BASE = 'https://markets.newyorkfed.org/api/soma/'

def _date(value):
    try:
        d = datetime.date.fromisoformat(value)
        if d.isoformat() != value:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('date must be YYYY-MM-DD')
    return d

def _get(path, key):
    r = requests.get(BASE + path, timeout=50)
    r.raise_for_status()
    a = r.json().get('soma', {}).get(key)
    if not isinstance(a, list):
        raise ValueError('unexpected SOMA response')
    return (a, r.url)

def summary(start, end, limit=1000):
    if _date(start) > _date(end) or not 1 <= limit <= 2000:
        raise ValueError('invalid range or limit')
    a, u = _get('summary.json', 'summary')
    a = [r for r in a if start <= r.get('asOfDate', '') <= end]
    return {'source': u, 'provider': 'Federal Reserve Bank of New York', 'unit': 'US dollars, see source for field definitions', 'matched_count': len(a), 'records': a[:limit]}

def treasury(asof, security_type='', limit=100):
    _date(asof)
    if not isinstance(security_type, str) or len(security_type) > 80 or (not 1 <= limit <= 1000):
        raise ValueError('invalid filter')
    a, u = _get('tsy/get/asof/' + asof + '.json', 'holdings')
    a = [r for r in a if not security_type or r.get('securityType', '').casefold() == security_type.casefold()]
    return {'source': u, 'provider': 'Federal Reserve Bank of New York', 'matched_count': len(a), 'records': a[:limit]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('summary')
    c.add_argument('start')
    c.add_argument('end')
    c.add_argument('--limit', type=int, default=1000)
    q = s.add_parser('treasury')
    q.add_argument('asof')
    q.add_argument('--security-type', default='')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    v = summary(a.start, a.end, a.limit) if a.cmd == 'summary' else treasury(a.asof, a.security_type, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
