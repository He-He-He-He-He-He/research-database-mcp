"""Read-only catalogue and variable metadata for Rwanda's Data Sharing Platform."""
import release_runtime
import argparse, json, uuid
import requests
BASE = 'https://api.data.gov.rw/api/v1/datasets/public'

def _read(url, params=None):
    r = requests.get(url, params=params, timeout=30, headers={'User-Agent': 'ResearchToolkit/1.0'})
    r.raise_for_status()
    body = r.json()
    if not body.get('success'):
        raise ValueError(body.get('message', 'Request failed'))
    return {'source': r.url, 'result': body['payload']}

def search(keyword='', page=1, limit=10):
    if not 1 <= limit <= 100 or page < 1:
        raise ValueError('page >= 1 and limit 1–100 required')
    return _read(BASE, {'search': keyword, 'page': page, 'limit': limit})

def metadata(dataset):
    dataset = str(uuid.UUID(dataset))
    return _read(BASE + '/' + dataset)

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword', nargs='?', default='')
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=10)
    a = s.add_parser('metadata')
    a.add_argument('dataset')
    a = p.parse_args()
    d = search(a.keyword, a.page, a.limit) if a.cmd == 'search' else metadata(a.dataset)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
