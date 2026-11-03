"""HM Land Registry UK house price index public linked-data JSON."""
import release_runtime
import argparse, json, re
import requests
ROOT = 'https://landregistry.data.gov.uk/'

def _get(path, params=None):
    with requests.get(ROOT + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 5 * 1024 * 1024:
                raise ValueError('response exceeds 5 MiB')
            parts.append(b)
        return {'source': r.url, 'data': json.loads(b''.join(parts))['result']}

def _region(region):
    if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', region) or len(region) > 100:
        raise ValueError('invalid region slug')
    return region

def month(region, date):
    region = _region(region)
    if not re.fullmatch('(19|20)\\d{2}-(0[1-9]|1[0-2])', date):
        raise ValueError('month must be YYYY-MM')
    d = _get(f'data/ukhpi/region/{region}/month/{date}.json')
    if 'primaryTopic' not in d['data']:
        raise ValueError('unknown region or month')
    return d

def latest(region, limit=12):
    region = _region(region)
    if not 1 <= limit <= 50:
        raise ValueError('limit must be 1–50')
    return _get('data/ukhpi.json', {'refRegion': 'http://landregistry.data.gov.uk/id/region/' + region, '_sort': '-refMonth', '_pageSize': limit, '_properties': 'averagePrice,housePriceIndex,percentageAnnualChange,refMonth'})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('month')
    a.add_argument('region')
    a.add_argument('date')
    a = s.add_parser('latest')
    a.add_argument('region')
    a.add_argument('--limit', type=int, default=12)
    a = p.parse_args()
    print(json.dumps(month(a.region, a.date) if a.cmd == 'month' else latest(a.region, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
