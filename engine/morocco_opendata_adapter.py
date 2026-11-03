"""Morocco government open data: CKAN discovery and bounded XLSX sheet reading."""
import release_runtime
import argparse
import io
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
API = 'https://data.gov.ma/data/api/3/action/'
MAX_BYTES = 15 * 1024 * 1024

def _get(url):
    import requests
    for _ in range(4):
        p = urlparse(url)
        if p.scheme != 'https' or p.hostname != 'data.gov.ma' or p.port not in (None, 443):
            raise ValueError('Only HTTPS data.gov.ma resources are supported')
        with requests.get(url, headers={'User-Agent': 'ResearchToolkit/1.0'}, timeout=35, stream=True, allow_redirects=False) as r:
            if r.is_redirect:
                from urllib.parse import urljoin
                url = urljoin(url, r.headers['Location'])
                continue
            r.raise_for_status()
            chunks = []
            total = 0
            for chunk in r.iter_content(65536):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError('Response exceeds 15 MiB')
                chunks.append(chunk)
            return b''.join(chunks)
    raise ValueError('Too many redirects')

def _action(name, **kwargs):
    from urllib.parse import urlencode
    url = API + name + '?' + urlencode(kwargs)
    data = json.loads(_get(url))
    if not data.get('success'):
        raise ValueError(str(data.get('error')))
    return {'source': url, 'result': data['result']}

def search(keyword, limit=10, offset=0):
    if not 1 <= limit <= 100 or offset < 0:
        raise ValueError('limit 1–100, offset >= 0')
    return _action('package_search', q=keyword, rows=limit, start=offset)

def metadata(dataset):
    return _action('package_show', id=dataset)

def sheet(dataset, resource, sheet_name='Data', offset=0, limit=20):
    if not 1 <= limit <= 200 or offset < 0:
        raise ValueError('limit 1–200, offset >= 0')
    meta = metadata(dataset)['result']
    matches = [r for r in meta.get('resources', []) if r.get('id') == resource]
    if not matches:
        raise ValueError('Resource not found in dataset')
    item = matches[0]
    if item.get('format', '').lower() != 'xlsx':
        raise ValueError('Only XLSX resources supported')
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(_get(item['url'])), read_only=True, data_only=True)
    try:
        if sheet_name not in wb.sheetnames:
            raise ValueError('Sheet not found; available: ' + ', '.join(wb.sheetnames))
        from itertools import islice
        rows = [[v.isoformat() if hasattr(v, 'isoformat') else v for v in row] for row in islice(wb[sheet_name].iter_rows(values_only=True), offset, offset + limit)]
        return {'source': item['url'], 'dataset': dataset, 'resource': resource, 'sheets': wb.sheetnames, 'sheet': sheet_name, 'offset': offset, 'rows': rows}
    finally:
        wb.close()

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=10)
    a.add_argument('--offset', type=int, default=0)
    a = s.add_parser('metadata')
    a.add_argument('dataset')
    a = s.add_parser('sheet')
    a.add_argument('dataset')
    a.add_argument('resource')
    a.add_argument('--sheet', default='Data')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    result = search(a.keyword, a.limit, a.offset) if a.cmd == 'search' else metadata(a.dataset) if a.cmd == 'metadata' else sheet(a.dataset, a.resource, a.sheet, a.offset, a.limit)
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
if __name__ == '__main__':
    main()
