"""Israel Central Bureau of Statistics time series and price indices APIs."""
import release_runtime
import argparse, json, re
import requests
SERIES = 'https://apis.cbs.gov.il/series/'
PRICE = 'https://api.cbs.gov.il/index/'

def _get(url, params):
    with requests.get(url, params={**params, 'format': 'json', 'download': 'false', 'lang': 'en'}, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(b)
        try:
            d = json.loads(b''.join(parts))
        except ValueError:
            raise ValueError('CBS did not return JSON') from None
        return {'source': r.url, 'data': d}

def catalog(level=1, subject=None, page=1, limit=50):
    if not 1 <= level <= 5 or not 1 <= page <= 10000 or (not 1 <= limit <= 100) or (level > 1 and (not isinstance(subject, int) or subject < 1)):
        raise ValueError('invalid catalog level, subject or paging')
    p = {'id': level, 'page': page, 'pagesize': limit}
    if subject is not None:
        p['subject'] = subject
    return _get(SERIES + 'catalog/level', p)

def path(code, page=1, limit=20):
    if not re.fullmatch('\\d+(?:,\\d+){0,4}', code) or not 1 <= page <= 10000 or (not 1 <= limit <= 100):
        raise ValueError('invalid path or paging')
    return _get(SERIES + 'data/path', {'id': code, 'data_hide': 'true', 'page': page, 'pagesize': limit})

def data(id, latest=12, page=1, limit=100):
    if not isinstance(id, int) or id < 1 or (not 1 <= latest <= 100) or (not 1 <= page <= 10000) or (not 1 <= limit <= 100):
        raise ValueError('invalid series or pagination')
    return _get(SERIES + 'data/list', {'id': id, 'last': latest, 'page': page, 'pagesize': limit})

def price(id, latest=12, page=1, limit=100):
    if not isinstance(id, int) or id < 1 or (not 1 <= latest <= 100) or (not 1 <= page <= 10000) or (not 1 <= limit <= 100):
        raise ValueError('invalid index or pagination')
    return _get(PRICE + 'data/price', {'id': id, 'last': latest, 'page': page, 'pagesize': limit})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('catalog')
    a.add_argument('--level', type=int, default=1)
    a.add_argument('--subject', type=int)
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=50)
    a = s.add_parser('path')
    a.add_argument('code')
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=20)
    for name in ['data', 'price']:
        a = s.add_parser(name)
        a.add_argument('id', type=int)
        a.add_argument('--latest', type=int, default=12)
        a.add_argument('--page', type=int, default=1)
        a.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    d = catalog(a.level, a.subject, a.page, a.limit) if a.cmd == 'catalog' else path(a.code, a.page, a.limit) if a.cmd == 'path' else data(a.id, a.latest, a.page, a.limit) if a.cmd == 'data' else price(a.id, a.latest, a.page, a.limit)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
