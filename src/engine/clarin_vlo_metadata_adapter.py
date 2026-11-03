"""Search CLARIN VLO public language resource metadata, not licensed corpora."""
import release_runtime
import argparse
import json
import requests
URL = 'https://vlo.clarin.eu/api/records'

def search(query, limit=5, offset=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('query must be 1–200 characters')
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit must be between 1 and 20')
    if not isinstance(offset, int) or not 0 <= offset <= 10000:
        raise ValueError('offset must be between 0 and 10000')
    r = requests.get(URL, params={'q': query.strip(), 'size': limit, 'from': offset}, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('records'), list):
        raise ValueError('Unexpected VLO response')
    records = []
    for row in data['records'][:limit]:
        f = row.get('fields') or {}
        records.append({'id': row.get('id'), 'name': f.get('name'), 'languageCode': f.get('languageCode'), 'resourceClass': f.get('resourceClass'), 'availability': f.get('availability'), 'license': f.get('license'), 'metadata_source': row.get('selflink'), 'landingPages': row.get('landingPages')})
    return {'source': 'CLARIN Virtual Language Observatory', 'query': query.strip(), 'numFound': data.get('numFound'), 'start': data.get('start'), 'records': records}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=5)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(search(a.query, a.limit, a.offset), ensure_ascii=False, indent=2))
