"""UN Economic Commission for Africa ECAStats public data portal."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://ecastats.uneca.org/ecastats.api/api'

def get(path, params=None):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, params=params, timeout=45, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 12000000:
                raise ValueError('Response exceeds 12 MB')
        j = json.loads(buf)
        if isinstance(j, dict) and j.get('isSuccess') is False:
            raise ValueError('Source API error: ' + str(j.get('errorMessage')))
        return (j, r.url)

def list_(name):
    if name not in ['topics', 'countries', 'dataSources']:
        raise ValueError('Invalid list')
    j, url = get('/' + name)
    return {'source': url, 'items': j.get('payload', j) if isinstance(j, dict) else j}

def indicators(topic, keyword=''):
    if not 1 <= topic <= 999999:
        raise ValueError('Invalid topic')
    j, url = get('/topic/indicators', {'topicId': topic})
    if not isinstance(j, list):
        raise ValueError('Unexpected indicator list')
    items = [x for x in j if keyword.casefold() in str(x.get('nameEn', '')).casefold()]
    return {'source': url, 'count': len(items), 'items': items}

def metadata(indicator):
    if not 1 <= indicator <= 99999999:
        raise ValueError('Invalid indicator')
    j, url = get('/SubIndicator/' + str(indicator))
    return {'source': url, 'metadata': j.get('payload')}

def data(indicator, country='', year=None, limit=100, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 1000000):
        raise ValueError('limit 1–1000; offset 0–1000000')
    if country and (not re.fullmatch('[A-Za-z]{3}', country)):
        raise ValueError('country must be ISO3')
    meta = metadata(indicator)
    j, url = get('/SubIndicator/timeSeries/' + str(indicator))
    items = j.get('payload')
    if not isinstance(items, list):
        raise ValueError('Unexpected data response')
    rows = [x for x in items if (not country or str(x.get('countryCode', '')).upper() == country.upper()) and (year is None or x.get('periodYear') == year)]
    selected = rows[offset:offset + limit]
    return {'source': url, 'metadata_source': meta['source'], 'metadata': meta['metadata'], 'matches': len(rows), 'returned': len(selected), 'offset': offset, 'next_offset': offset + len(selected) if offset + len(selected) < len(rows) else None, 'truncated': offset + len(selected) < len(rows), 'rows': selected, 'note': 'Each request refetches the full upstream series and slices locally; source ordering and values may change across requests. ECAStats aggregates multiple producers; check each row source, status and original methodology. Source metadata may conflict with reported value units; do not convert without independent confirmation.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('list')
    c.add_argument('name', choices=['topics', 'countries', 'dataSources'])
    i = s.add_parser('indicators')
    i.add_argument('topic', type=int)
    i.add_argument('--keyword', default='')
    m = s.add_parser('metadata')
    m.add_argument('id', type=int)
    d = s.add_parser('data')
    d.add_argument('id', type=int)
    d.add_argument('--country', default='')
    d.add_argument('--year', type=int)
    d.add_argument('--limit', type=int, default=100)
    d.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    res = list_(a.name) if a.cmd == 'list' else indicators(a.topic, a.keyword) if a.cmd == 'indicators' else metadata(a.id) if a.cmd == 'metadata' else data(a.id, a.country, a.year, a.limit, a.offset)
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
