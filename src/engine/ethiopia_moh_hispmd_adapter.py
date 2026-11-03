"""Ethiopian Ministry of Health HIS performance dashboard public JSON."""
import release_runtime
import argparse, json
import requests
URL = 'https://hispmd.moh.gov.et/api/dash/hispmd_data.php'

def fetch():
    session = requests.Session()
    session.trust_env = False
    with session.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        content = bytearray()
        for chunk in r.iter_content(65536):
            content.extend(chunk)
            if len(content) > 5000000:
                raise ValueError('Response exceeds 5 MB')
        data = json.loads(content)
        if not isinstance(data, list) or not all((isinstance(x, dict) and 'indicator' in x for x in data)):
            raise ValueError('Unexpected source response')
        return data

def query(keyword='', group='', scope='', year=None, limit=100):
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1–1000')
    data = fetch()
    matches = [x for x in data if keyword.casefold() in str(x.get('indicator', '')).casefold() and group.casefold() in str(x.get('Indicator Group', '')).casefold() and (scope.casefold() in str(x.get('Scope', '')).casefold()) and (year is None or str(x.get('Year')) == str(year))]
    return {'source': URL, 'total_matches': len(matches), 'returned': min(len(matches), limit), 'truncated': len(matches) > limit, 'rows': matches[:limit], 'note': 'Source is health information-system performance, not general population health statistics. Verify original period, geography, representation, and data source.'}

def catalog():
    data = fetch()
    groups = {}
    for x in data:
        group = str(x.get('Indicator Group', ''))
        groups.setdefault(group, set()).add(str(x.get('indicator', '')))
    return {'source': URL, 'row_count': len(data), 'indicator_groups': {k: sorted(v) for k, v in groups.items()}}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('catalog')
    q = s.add_parser('data')
    q.add_argument('--keyword', default='')
    q.add_argument('--group', default='')
    q.add_argument('--scope', default='')
    q.add_argument('--year', type=int)
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(catalog() if a.command == 'catalog' else query(a.keyword, a.group, a.scope, a.year, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
