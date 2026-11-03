"""WFP market food prices, distributed by OCHA Humanitarian Data Exchange."""
import release_runtime
import argparse, csv, json, re, requests
BASE = 'https://data.humdata.org/api/3/action/'

def dataset(slug):
    if not isinstance(slug, str) or not re.fullmatch('wfp-food-prices-for-[a-z0-9-]{1,70}', slug):
        raise ValueError('expected WFP food prices country dataset slug')
    r = requests.get(BASE + 'package_show', params={'id': slug}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not j.get('success') or j['result'].get('organization', {}).get('name') != 'wfp':
        raise ValueError('not a WFP dataset')
    return j['result']

def prices(slug, year, commodity=None, market=None, limit=100):
    if isinstance(year, bool) or not 1900 <= int(year) <= 2100:
        raise ValueError('invalid year')
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    for x in (commodity, market):
        if x is not None and (not isinstance(x, str) or len(x) > 100):
            raise ValueError('invalid filter')
    d = dataset(slug)
    resources = [x for x in d.get('resources', []) if x.get('name', '').endswith(' - Food Prices') and x.get('format', '').upper() == 'CSV']
    if len(resources) != 1:
        raise ValueError('Expected one WFP food-price resource')
    u = resources[0]['url']
    if not re.fullmatch('https://data\\.humdata\\.org/dataset/[a-f0-9-]+/resource/[a-f0-9-]+/download/[A-Za-z0-9_.-]+\\.csv', u):
        raise ValueError('Unexpected resource URL')
    with requests.get(u, timeout=120, stream=True) as r:
        r.raise_for_status()
        r.encoding = 'utf-8-sig'
        n = 0

        def lines():
            nonlocal n
            for line in r.iter_lines(decode_unicode=True):
                n += len(line) + 1
                if n > 100000000:
                    raise ValueError('CSV exceeds 100 MB limit')
                yield line
        reader = csv.DictReader(lines())
        need = {'date', 'market', 'commodity', 'unit', 'currency', 'price', 'pricetype', 'priceflag'}
        if not need.issubset(reader.fieldnames or []):
            raise ValueError('unexpected CSV schema')
        out = []
        count = 0
        for x in reader:
            if not x['date'].startswith(str(year) + '-'):
                continue
            if commodity and x['commodity'].casefold() != commodity.casefold():
                continue
            if market and x['market'].casefold() != market.casefold():
                continue
            count += 1
            if len(out) < limit:
                out.append(x)
    return {'provider': 'World Food Programme Price Database', 'dataset_sources': d.get('dataset_source'), 'distributor': 'OCHA HDX', 'dataset': slug, 'metadata_url': BASE + 'package_show?id=' + slug, 'source': u, 'license': d.get('license_title'), 'last_modified': d.get('last_modified'), 'matched_count': count, 'returned_count': len(out), 'records': out, 'note': 'Keep unit, currency, market, price type and price flag; blank means missing, not zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('slug')
    p.add_argument('year', type=int)
    p.add_argument('--commodity')
    p.add_argument('--market')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(prices(a.slug, a.year, a.commodity, a.market, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
