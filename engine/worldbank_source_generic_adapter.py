"""World Bank Indicators API: discover sources, dimensions and bounded values."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/'
MAX = 8000000

def _id(v, pattern, label):
    if not isinstance(v, str) or not re.fullmatch(pattern, v):
        raise ValueError('invalid ' + label)
    return v

def _get(path, per_page=500, page=1):
    with requests.get(BASE + path, params={'format': 'json', 'per_page': per_page, 'page': page}, timeout=35, stream=True) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for x in r.iter_content(65536):
            n += len(x)
            if n > MAX:
                raise ValueError('World Bank response exceeds 8 MB')
            chunks.append(x)
        url = r.url
    try:
        j = json.loads(b''.join(chunks))
    except ValueError:
        raise ValueError('World Bank returned non-JSON') from None
    if isinstance(j, list) and len(j) == 1 and isinstance(j[0], dict) and ('message' in j[0]):
        raise ValueError('World Bank returned API error')
    return (j, url)

def sources(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('invalid keyword')
    j, u = _get('', 100, 1)
    if not isinstance(j, list) or len(j) != 2 or int(j[0].get('pages', 0)) > 1 or (not isinstance(j[1], list)):
        raise ValueError('unexpected or paginated sources')
    hits = [x for x in j[1] if keyword.casefold() in (str(x.get('id', '')) + ' ' + str(x.get('name', ''))).casefold()]
    return {'source': u, 'total': len(j[1]), 'matched': len(hits), 'sources': hits, 'note': 'Availability and collection status vary. Historical, retired and third-party compilations may appear.'}

def catalog(source, kind, keyword='', page=1):
    source = _id(source, '[0-9]{1,4}', 'source')
    if kind not in ('country', 'series'):
        raise ValueError('kind must be country or series')
    if not isinstance(keyword, str) or len(keyword) > 150 or isinstance(page, bool) or (not isinstance(page, int)) or (not 1 <= page <= 1000):
        raise ValueError('invalid keyword or page')
    j, u = _get(source + '/' + kind, 500, page)
    try:
        v = j['source'][0]['concept'][0]['variable']
    except (KeyError, IndexError, TypeError):
        raise ValueError('unexpected source catalogue response') from None
    if not isinstance(v, list):
        raise ValueError('unexpected catalogue records')
    hits = [x for x in v if keyword.casefold() in (str(x.get('id', '')) + ' ' + str(x.get('value', ''))).casefold()]
    return {'source': u, 'page': j['page'], 'pages': j['pages'], 'dataset_total': j['total'], 'matched_on_page': len(hits), 'records': hits, 'note': 'Keyword matches only this page; inspect all pages to exhaust catalogue.'}

def catalog_all(source, kind, keyword='', limit=100, offset=0):
    source = _id(source, '[0-9]{1,4}', 'source')
    if kind not in ('country', 'series') or not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('invalid kind or keyword')
    if type(limit) is not int or not 1 <= limit <= 500 or type(offset) is not int or (not 0 <= offset <= 100000):
        raise ValueError('invalid limit or offset')
    rows = []
    expected_total = None
    expected_pages = None
    seen = set()
    for page in range(1, 21):
        j, u = _get(source + '/' + kind, 500, page)
        try:
            values = j['source'][0]['concept'][0]['variable']
            actual = j['page']
            pages = j['pages']
            total = j['total']
        except (KeyError, IndexError, TypeError):
            raise ValueError('unexpected source catalogue response') from None
        if type(actual) is not int or actual != page or type(pages) is not int or (not 1 <= pages <= 20) or (type(total) is not int) or (total < 0) or (not isinstance(values, list)) or (len(values) > 500):
            raise ValueError('catalogue page metadata invalid or exceeds 20 pages')
        if expected_total is None:
            expected_total = total
            expected_pages = pages
        if total != expected_total or pages != expected_pages:
            raise ValueError('catalogue changed during pagination; retry')
        for x in values:
            if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('value'), str)) or (x['id'] in seen):
                raise ValueError('missing or repeated catalogue identifier')
            seen.add(x['id'])
            rows.append(x)
        if page == pages:
            break
    else:
        raise ValueError('catalogue exceeds 20 pages')
    if len(rows) != expected_total:
        raise ValueError('catalogue count mismatch; retry')
    matches = [x for x in rows if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': BASE + source + '/' + kind, 'source_id': source, 'kind': kind, 'catalog_total': expected_total, 'source_pages_fetched': expected_pages, 'matched_total': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(matches) else None, 'records': matches[offset:offset + limit], 'note': 'Fetches up to 20 source pages and checks totals and identifiers before local keyword filtering. No source snapshot guarantee: concurrent changes may still affect results. Repeated requests may return a different order; labels and coverage are provider metadata.'}

def metadata(source, indicator):
    source = _id(source, '[0-9]{1,4}', 'source')
    indicator = _id(indicator, '[A-Za-z0-9_.-]{1,100}', 'indicator')
    j, u = _get(source + '/series/' + indicator + '/metadata')
    try:
        x = j['source'][0]['concept'][0]['variable'][0]
    except (KeyError, IndexError, TypeError):
        raise ValueError('indicator metadata unavailable') from None
    if x.get('id') != indicator:
        raise ValueError('unexpected metadata indicator')
    return {'source': u, 'indicator': indicator, 'metadata': x.get('metatype', [])}

def observations(source, country, indicator, start, end):
    source = _id(source, '[0-9]{1,4}', 'source')
    country = _id(country, '[A-Z0-9]{3}', 'country')
    indicator = _id(indicator, '[A-Za-z0-9_.-]{1,100}', 'indicator')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1800 <= start <= end <= 2100:
        raise ValueError('invalid years')
    j, u = _get(source + '/country/' + country + '/series/' + indicator + '/time/all')
    data = j.get('source', {}) if isinstance(j, dict) else {}
    if int(j.get('pages', 0)) != 1 or not isinstance(data, dict) or data.get('id') != source or (not isinstance(data.get('data'), list)):
        raise ValueError('unexpected or paginated observation response')
    out = []
    for row in data['data']:
        dims = {x['concept']: {'code': x['id'], 'name': x['value']} for x in row['variable']}
        if dims.get('Country', {}).get('code') != country or dims.get('Series', {}).get('code') != indicator:
            raise ValueError('upstream dimensions do not match request')
        time = str(dims.get('Time', {}).get('name', ''))
        if not re.fullmatch('\\d{4}', time):
            raise ValueError('nonannual period; this generic adapter supports annual data only')
        if start <= int(time) <= end:
            out.append({'year': int(time), 'raw_value': row.get('value'), 'dimensions': dims})
    return {'source': u, 'database': data.get('name'), 'last_updated': j.get('lastupdated'), 'observations': out, 'note': 'Check indicator metadata and original provider for units, vintage, methods, licence and forecast status; null is missing. Other sources may repeat same underlying figures.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('sources')
    q.add_argument('--keyword', default='')
    q = sub.add_parser('catalog')
    q.add_argument('source')
    q.add_argument('kind', choices=['country', 'series'])
    q.add_argument('--keyword', default='')
    q.add_argument('--page', type=int, default=1)
    q = sub.add_parser('metadata')
    q.add_argument('source')
    q.add_argument('indicator')
    q = sub.add_parser('data')
    q.add_argument('source')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    a = p.parse_args()
    try:
        r = sources(a.keyword) if a.cmd == 'sources' else catalog(a.source, a.kind, a.keyword, a.page) if a.cmd == 'catalog' else metadata(a.source, a.indicator) if a.cmd == 'metadata' else observations(a.source, a.country, a.indicator, a.start, a.end)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    except (ValueError, requests.RequestException) as e:
        p.exit(1, str(e) + '\n')
if __name__ == '__main__':
    main()
