"""UN DESA Population Division DemoData: source-preserving empirical data API."""
import release_runtime
import argparse
import json
import urllib.parse
import requests
BASE = 'https://population.un.org/demodata-api/api/'
MAX_BYTES = 12000000

def fetch(endpoint, params=None):
    url = BASE + endpoint
    if params:
        url += '?' + urllib.parse.urlencode(params)
    with requests.get(url, headers={'User-Agent': 'ResearchToolkit/1.0', 'Accept': 'application/json'}, timeout=60, stream=True) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError('Response exceeds 12 MB; narrow the location and indicator.')
            chunks.append(chunk)
        body = b''.join(chunks)
    if len(body) > MAX_BYTES:
        raise ValueError('Response exceeds 12 MB; narrow the location and indicator.')
    payload = json.loads(body)
    if not payload.get('success') or not isinstance(payload.get('data'), list):
        raise ValueError('API returned an error or unexpected response: ' + str(payload)[:400])
    return (payload['data'], url)

def query(kind, location=None, indicator=None, keyword=None, start=None, end=None, limit=100, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 1000000):
        raise ValueError('limit must be 1–1000 and offset 0–1000000')
    if kind == 'data':
        if location is None or indicator is None:
            raise ValueError('data requires location and indicator IDs')
        items, url = fetch('structuredDataDetailed', {'locIDs': int(location), 'indicatorIDs': int(indicator)})
        if start is not None:
            items = [x for x in items if x.get('timeMid') is not None and x['timeMid'] >= start]
        if end is not None:
            items = [x for x in items if x.get('timeMid') is not None and x['timeMid'] < end + 1]
        indicators, _ = fetch('indicators')
        metadata = next((x for x in indicators if x.get('indicatorId') == int(indicator)), None)
    elif kind == 'catalog':
        if location is None:
            raise ValueError('catalog requires location ID')
        items, url = fetch('dataCatalogs', {'locIds': int(location)})
        metadata = None
    elif kind in ('locations', 'indicators'):
        items, url = fetch(kind)
        metadata = None
    else:
        raise ValueError('Unknown query type')
    if keyword:
        term = keyword.casefold()
        items = [x for x in items if term in json.dumps(x, ensure_ascii=False).casefold()]
    selected = items[offset:offset + limit]
    return {'provider': 'UN DESA Population Division DemoData', 'request_url': url, 'indicator_metadata': metadata, 'matched_count': len(items), 'returned_count': len(selected), 'limit': limit, 'offset': offset, 'next_offset': offset + len(selected) if offset + len(selected) < len(items) else None, 'truncated': offset + len(selected) < len(items), 'records': selected, 'note': 'Offsets slice the locally fetched result; each request refetches the full source and source ordering or values may change. Observation midpoint filters are local and are not publication-year filters. The API is not paginated here.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=['locations', 'indicators', 'catalog', 'data'])
    p.add_argument('--location', type=int)
    p.add_argument('--indicator', type=int)
    p.add_argument('--keyword')
    p.add_argument('--start', type=int)
    p.add_argument('--end', type=int)
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.location, a.indicator, a.keyword, a.start, a.end, a.limit, a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
