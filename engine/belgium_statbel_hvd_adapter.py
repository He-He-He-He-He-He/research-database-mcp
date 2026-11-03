"""Belgian Statbel public High Value Datasets: introspect and query."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://opendata-api.statbel.fgov.be'

def get(path, params=None):
    session = requests.Session()
    session.trust_env = False
    with session.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 8000000:
                raise ValueError('Response exceeds 8 MB; narrow your selection')
        return (json.loads(buf), r.url)

def spec():
    return get('/')[0]

def catalog():
    s = spec()
    return {'source': BASE + '/', 'datasets': [p[1:] for p in s['paths'] if p.startswith('/tf_')]}

def schema(table):
    s = spec()
    if '/' + table not in s['paths'] or not table.startswith('tf_'):
        raise ValueError('Unknown dataset')
    return {'source': BASE + '/', 'table': table, 'schema': s['definitions'][table]}

def data(table, filters, limit, offset, order):
    schema_ = schema(table)['schema']['properties']
    if not 1 <= limit <= 1000 or not 0 <= offset <= 1000000:
        raise ValueError('limit 1–1000; offset 0–1000000')
    params = {'limit': limit, 'offset': offset}
    for pair in filters:
        if '=' not in pair:
            raise ValueError('Use FIELD=VALUE')
        k, v = pair.split('=', 1)
        if k not in schema_ or not re.fullmatch('[\\w .-]{1,100}', v):
            raise ValueError('Invalid filter field or value')
        params[k] = 'eq.' + v
    if order:
        if order not in schema_:
            raise ValueError('Invalid ordering field')
        params['order'] = order + '.desc'
    rows, url = get('/' + table, params)
    if not isinstance(rows, list):
        raise ValueError('Unexpected response shape')
    return {'source': url, 'dataset': table, 'count_returned': len(rows), 'limit': limit, 'offset': offset, 'rows': rows, 'note': 'See official dataset documentation for methodology and units; verify all dimensions and reference periods.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('catalog')
    m = s.add_parser('schema')
    m.add_argument('table')
    d = s.add_parser('data')
    d.add_argument('table')
    d.add_argument('--filter', action='append', default=[])
    d.add_argument('--limit', type=int, default=20)
    d.add_argument('--offset', type=int, default=0)
    d.add_argument('--order-desc')
    a = p.parse_args()
    result = catalog() if a.command == 'catalog' else schema(a.table) if a.command == 'schema' else data(a.table, a.filter, a.limit, a.offset, a.order_desc)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
