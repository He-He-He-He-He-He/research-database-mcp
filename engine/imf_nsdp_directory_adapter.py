"""IMF DSBB worldwide national summary data page directory (discovery only)."""
import release_runtime
import argparse, json
import requests
BASE = 'https://dsbb.imf.org/api/country/getAllNSDPCountries'
PARAMS = {'clientLocPath': 'https://dsbb.imf.org/nsdp', 'ContainerID': 'DSBBMaster'}

def countries(query='', limit=50):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError('查询词无效')
    if not 1 <= limit <= 200:
        raise ValueError('limit 应在 1–200')
    s = requests.Session()
    s.trust_env = False
    r = s.get(BASE, params=PARAMS, timeout=30)
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('响应过大')
    items = r.json()
    if not isinstance(items, list) or any((not isinstance(x, dict) or 'CountryCode' not in x or 'CountryName' not in x for x in items)):
        raise ValueError('官方目录数据结构异常')
    q = query.casefold().strip()
    out = [{'code': x.get('CountryCode'), 'name': x.get('CountryName'), 'nsdp_url': x.get('NSDPUrl')} for x in items if q in (str(x.get('CountryCode', '')) + ' ' + str(x.get('CountryName', ''))).casefold()]
    return {'source': 'https://dsbb.imf.org/nsdp', 'api': BASE, 'total': len(out), 'returned': min(limit, len(out)), 'countries': out[:limit], 'note': '仅发现 IMF 登记的国家汇总数据页，不代表链接目前可用、可机读或资料最新。各系列来源、时点和单位须核查该国页面。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query', nargs='?', default='')
    p.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    print(json.dumps(countries(a.query, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
