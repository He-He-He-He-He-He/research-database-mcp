"""UK Food Standards Agency public food hygiene ratings API v2."""
import release_runtime
import argparse, json
import requests
ROOT = 'https://api.ratings.food.gov.uk/'

def _get(path, params=None):
    with requests.get(ROOT + path, params=params, timeout=30, stream=True, headers={'x-api-version': '2', 'Accept': 'application/json', 'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        return {'source': r.url, 'data': json.loads(b''.join(parts))}

def authorities():
    return _get('Authorities')

def establishment(id):
    if not isinstance(id, int) or id < 1:
        raise ValueError('invalid FHRS ID')
    return _get('Establishments/' + str(id))

def search(name, address='', authority=None, page=1, limit=20):
    if not name or len(name) > 120 or len(address) > 120 or (not 1 <= page <= 10000) or (not 1 <= limit <= 100):
        raise ValueError('invalid search')
    p = {'name': name, 'pageNumber': page, 'pageSize': limit}
    if address:
        p['address'] = address
    if authority is not None:
        if not isinstance(authority, int) or authority < 1:
            raise ValueError('invalid local authority')
        p['localAuthorityId'] = authority
    return _get('Establishments', p)

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('authorities')
    a = s.add_parser('establishment')
    a.add_argument('id', type=int)
    a = s.add_parser('search')
    a.add_argument('name')
    a.add_argument('--address', default='')
    a.add_argument('--authority', type=int)
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    result = authorities() if a.cmd == 'authorities' else establishment(a.id) if a.cmd == 'establishment' else search(a.name, a.address, a.authority, a.page, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
