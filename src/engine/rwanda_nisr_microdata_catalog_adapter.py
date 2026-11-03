"""Rwanda National Institute of Statistics public survey catalog metadata."""
import release_runtime
import requests
URL = 'https://microdatabk.statistics.gov.rw/api/catalog/search'

def search(keyword='', limit=20):
    if not isinstance(keyword, str) or len(keyword) > 200 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('keyword <=200 characters; limit 1..100')
    r = requests.get(URL, params={'ps': 100}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    if payload.get('status') != 'success':
        raise ValueError('Catalog did not return success')
    data = payload['result']
    rows = data['rows']
    found = int(data['found'])
    if found != len(rows):
        raise ValueError('Catalog exceeds one verified page or response incomplete; do not assume complete results')
    term = keyword.casefold().strip()
    matches = [row for row in rows if not term or term in ' '.join((str(row.get(k) or '') for k in ('title', 'subtitle', 'abstract', 'idno', 'authoring_entity'))).casefold()]
    return {'source': URL, 'catalog_total': found, 'matched_total': len(matches), 'limit': limit, 'returned': min(limit, len(matches)), 'truncated': len(matches) > limit, 'records': matches[:limit], 'notes': ['Official NISR public catalog metadata, searched locally across title, subtitle, abstract, idno and authoring entity; not statistical observations or permission to download microdata.', 'Survey years, catalog creation/change times and download/view counts are distinct; access and use conditions must be checked on the study page.', 'Increase limit up to 100 when truncated; if the catalog grows beyond 100 records this adapter fails rather than presenting an incomplete search as complete.']}
