"""Statistics Austria open-data catalogue, metadata and bounded CSV rows."""
import release_runtime
import argparse, csv, io, json, re
import requests
from bs4 import BeautifulSoup
BASE = 'https://data.statistik.gv.at'
MAX = 15 * 1024 * 1024

def _read(path, params=None):
    with requests.get(BASE + path, params=params, timeout=40, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}, allow_redirects=False) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for part in r.iter_content(65536):
            size += len(part)
            if size > MAX:
                raise ValueError('Response exceeds 15 MiB')
            chunks.append(part)
        return (r.url, b''.join(chunks))

def _id(x):
    if not re.fullmatch('OGD[A-Za-z0-9_-]{1,150}', x):
        raise ValueError('Invalid dataset id')
    return x

def search(keyword, limit=20):
    if not keyword or len(keyword) > 120 or (not 1 <= limit <= 100):
        raise ValueError('invalid search')
    url, b = _read('/web/catalog.jsp')
    soup = BeautifulSoup(b, 'html.parser')
    out = []
    seen = set()
    for row in soup.select('tr'):
        a = row.select_one('td h4 a[aria-label^="OGD_"]')
        if not a:
            continue
        i = a.get('aria-label')
        title = a.get_text(' ', strip=True)
        if i not in seen and keyword.casefold() in (title + ' ' + i).casefold():
            seen.add(i)
            out.append({'id': i, 'title': title})
    return {'source': url, 'count': len(out), 'results': out[:limit]}

def metadata(dataset):
    url, b = _read('/ogd/json', {'dataset': _id(dataset)})
    return {'source': url, 'metadata': json.loads(b)}

def rows(dataset, resource=None, limit=20, offset=0):
    if not 1 <= limit <= 200 or offset < 0:
        raise ValueError('invalid limit/offset')
    m = metadata(dataset)['metadata']
    resource = resource or dataset
    match = [r for r in m.get('resources', []) if r.get('name') == resource and r.get('format', '').lower() == 'csv']
    if not match:
        raise ValueError('CSV resource not found in metadata')
    from urllib.parse import urlparse
    p = urlparse(match[0]['url'])
    if p.scheme != 'https' or p.hostname != 'data.statistik.gv.at' or p.port not in (None, 443):
        raise ValueError('Unexpected resource host')
    url, b = _read(p.path)
    reader = csv.DictReader(io.StringIO(b.decode('utf-8-sig')), delimiter=';')
    from itertools import islice
    return {'source': url, 'columns': reader.fieldnames, 'offset': offset, 'rows': list(islice(reader, offset, offset + limit))}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('metadata')
    a.add_argument('dataset')
    a = s.add_parser('rows')
    a.add_argument('dataset')
    a.add_argument('--resource')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.dataset) if a.cmd == 'metadata' else rows(a.dataset, a.resource, a.limit, a.offset)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
