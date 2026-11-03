"""UN-Habitat Urban Indicators catalog and bounded public feature rows."""
import release_runtime
import argparse, json, re
from urllib.parse import urlparse
import requests
ROOT = 'https://data.unhabitat.org/api/search/v1/'
ORG = 'uWtJiVzcBsV6C7NV'
MAX = 8 * 1024 * 1024

def _get(url, params=None):
    with requests.get(url, params=params, timeout=30, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX:
                raise ValueError('response exceeds 8 MiB')
            parts.append(b)
        d = json.loads(b''.join(parts))
        if 'error' in d:
            raise ValueError(str(d['error']))
        return {'source': r.url, 'result': d}

def search(keyword, limit=20):
    if not keyword or len(keyword) > 120 or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    return _get(ROOT + 'collections/dataset/items', {'q': keyword, 'limit': limit})

def metadata(item):
    if not re.fullmatch('[0-9a-f]{32}', item):
        raise ValueError('invalid item ID')
    return _get(ROOT + 'collections/dataset/items/' + item)

def _service(item):
    d = metadata(item)['result']
    p = d['properties']
    url = p.get('url')
    u = urlparse(url or '')
    if p.get('access') != 'public' or p.get('type') not in ('Feature Service', 'Feature Layer', 'Table') or u.scheme != 'https' or (u.hostname != 'services6.arcgis.com') or (not u.path.startswith('/' + ORG + '/arcgis/rest/services/')) or (not u.path.endswith('/FeatureServer')) or u.query or u.fragment:
        raise ValueError('Not an approved public UN-Habitat feature service')
    return url.rstrip('/')

def layer(item, layer_id=0):
    if not isinstance(layer_id, int) or not 0 <= layer_id <= 1000:
        raise ValueError('invalid layer')
    return _get(_service(item) + '/' + str(layer_id), {'f': 'json'})

def rows(item, layer_id, field, value, fields, limit=20, offset=0):
    if not isinstance(value, str) or len(value) > 100 or (not value) or (not 1 <= limit <= 100) or (offset < 0):
        raise ValueError('invalid filter or pagination')
    info = layer(item, layer_id)
    allowed = {x['name'] for x in info['result'].get('fields', [])}
    if field not in allowed or not fields or len(fields) > 30 or any((x not in allowed for x in fields)):
        raise ValueError('unknown field; inspect layer metadata')
    where = field + " = '" + value.replace("'", "''") + "'"
    return _get(info['source'].split('?')[0] + '/query', {'f': 'json', 'where': where, 'outFields': ','.join(fields), 'returnGeometry': 'false', 'resultRecordCount': limit, 'resultOffset': offset})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('metadata')
    a.add_argument('item')
    a = s.add_parser('layer')
    a.add_argument('item')
    a.add_argument('--layer', type=int, default=0)
    a = s.add_parser('rows')
    a.add_argument('item')
    a.add_argument('field')
    a.add_argument('value')
    a.add_argument('--fields', required=True)
    a.add_argument('--layer', type=int, default=0)
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.item) if a.cmd == 'metadata' else layer(a.item, a.layer) if a.cmd == 'layer' else rows(a.item, a.layer, a.field, a.value, a.fields.split(','), a.limit, a.offset)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
