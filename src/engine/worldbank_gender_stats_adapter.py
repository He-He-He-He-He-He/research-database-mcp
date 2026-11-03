"""World Bank Gender Statistics source 14."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/14/'

def get(path, page=1):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 500, 'page': page}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or unavailable data')
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return (j, r.url)

def catalog(kind, keyword='', page=1):
    if kind not in {'country', 'series'}:
        raise ValueError('invalid dimension')
    if not isinstance(keyword, str) or len(keyword) > 100 or isinstance(page, bool) or (not isinstance(page, int)) or (not 1 <= page <= 100):
        raise ValueError('invalid query')
    j, u = get(kind, page)
    v = j['source'][0]['concept'][0]['variable']
    rows = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'page': j['page'], 'pages': j['pages'], 'dataset_total': j['total'], 'matched_on_page': len(rows), 'records': rows, 'note': 'Keyword applies only to this page; inspect all pages to exhaust catalog.'}

def catalog_all(kind, keyword='', limit=100, offset=0):
    """Fetch and check all source pages, then filter locally; not an atomic snapshot."""
    if kind not in {'country', 'series'} or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid catalog query')
    if type(limit) is not int or not 1 <= limit <= 1000 or type(offset) is not int or (offset < 0):
        raise ValueError('invalid limit or offset')
    rows = []
    seen = set()
    urls = []
    page = 1
    expected_pages = None
    expected_total = None
    while expected_pages is None or page <= expected_pages:
        j, u = get(kind, page)
        urls.append(u)
        if any((type(j.get(k)) is not int for k in ('page', 'pages', 'total', 'per_page'))) or j['page'] != page or (not 1 <= j['pages'] <= 20) or (j['total'] < 0) or (j['per_page'] != 500):
            raise ValueError('unexpected World Bank pagination metadata')
        if expected_pages is None:
            expected_pages = j['pages']
            expected_total = j['total']
        if j['pages'] != expected_pages or j['total'] != expected_total:
            raise ValueError('catalog changed while reading pages')
        batch = j['source'][0]['concept'][0]['variable']
        if not isinstance(batch, list) or len(batch) > 500 or (page < expected_pages and len(batch) != 500):
            raise ValueError('incomplete World Bank catalog page')
        for item in batch:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or item['id'] in seen:
                raise ValueError('invalid or duplicate catalog ID')
            seen.add(item['id'])
            rows.append(item)
        page += 1
    if len(rows) != expected_total:
        raise ValueError('catalog count changed or incomplete')
    hits = [x for x in rows if keyword.casefold() in (x['id'] + ' ' + str(x.get('value', ''))).casefold()]
    return {'sources': urls, 'dataset_total': expected_total, 'matched': len(hits), 'offset': offset, 'returned': len(hits[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(hits) else None, 'truncated': offset + limit < len(hits), 'records': hits[offset:offset + limit], 'note': 'Locally filtered all pages observed in this run; the source can change during or between requests, so this is not an atomic snapshot. Country and aggregate entries may overlap.'}

def metadata(indicator):
    if not re.fullmatch('[A-Za-z0-9._-]{3,80}', indicator):
        raise ValueError('invalid indicator')
    j, u = get('series/' + indicator + '/metadata')
    v = j['source'][0]['concept'][0]['variable'][0]
    if v['id'] != indicator:
        raise ValueError('unexpected indicator metadata')
    return {'source': u, 'indicator': indicator, 'metadata': v['metatype']}

def observations(country, indicator, start, end):
    if not re.fullmatch('[A-Z0-9]{3}', country) or not re.fullmatch('[A-Za-z0-9._-]{3,80}', indicator):
        raise ValueError('invalid country or indicator')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    j, u = get(f'country/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if j['pages'] != 1 or not isinstance(s, dict) or s.get('id') != '14' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected or paginated data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        year = int(dims['Time']['name'])
        if start <= year <= end:
            out.append({'year': year, 'raw_value': x['value'], 'dimensions': dims})
    return {'source': u, 'provider': 'World Bank Gender Statistics', 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Compilation includes other organizations data. Consult series metadata for source, definition, scale and reuse conditions. Null means missing.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series'])
    c.add_argument('--keyword', default='')
    c.add_argument('--page', type=int, default=1)
    m = s.add_parser('metadata')
    m.add_argument('indicator')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    a = p.parse_args()
    result = catalog(a.kind, a.keyword, a.page) if a.cmd == 'catalog' else metadata(a.indicator) if a.cmd == 'metadata' else observations(a.country, a.indicator, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
