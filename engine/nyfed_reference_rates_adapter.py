"""Federal Reserve Bank of New York overnight reference rates API."""
import release_runtime
import argparse, datetime, json, requests
PATHS = {'SOFR': 'secured/sofr', 'BGCR': 'secured/bgcr', 'TGCR': 'secured/tgcr', 'EFFR': 'unsecured/effr', 'OBFR': 'unsecured/obfr'}
BASE = 'https://markets.newyorkfed.org/api/rates/'

def observations(rate, start, end):
    if rate not in PATHS:
        raise ValueError('unknown reference rate')
    try:
        a, b = (datetime.date.fromisoformat(start), datetime.date.fromisoformat(end))
        if a.isoformat() != start or b.isoformat() != end or a > b or ((b - a).days > 3660):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('dates must be YYYY-MM-DD, ordered and within 3660 days')
    url = BASE + PATHS[rate] + '/search.json'
    response = requests.get(url, params={'startDate': start, 'endDate': end}, timeout=40)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('refRates'), list):
        raise ValueError('unexpected upstream response')
    return {'provider': 'Federal Reserve Bank of New York', 'source': response.url, 'rate': rate, 'unit': 'percent per year', 'volume_unit': 'billions of US dollars', 'records': data['refRates']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rate', choices=PATHS)
    p.add_argument('start')
    p.add_argument('end')
    a = p.parse_args()
    print(json.dumps(observations(a.rate, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
