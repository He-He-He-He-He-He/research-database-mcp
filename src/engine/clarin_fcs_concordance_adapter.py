"""Bounded CLARIN FCS concordance lookup for one publicly accessible resource."""
import release_runtime
import time
import requests
BASE = 'https://contentsearch.clarin.eu/rest'

def search(query, resource_id, limit=3):
    if not isinstance(query, str) or not query.strip() or len(query) > 100:
        raise ValueError('query must be 1–100 characters')
    if not isinstance(resource_id, str) or not resource_id or len(resource_id) > 1000:
        raise ValueError('resource_id required')
    if not isinstance(limit, int) or not 1 <= limit <= 5:
        raise ValueError('limit must be 1–5')
    s = requests.Session()
    directory = s.get(BASE + '/resources', timeout=30)
    directory.raise_for_status()
    matches = [x for x in directory.json() if x.get('id') == resource_id]
    if len(matches) != 1 or matches[0].get('availabilityRestriction') != 'NONE':
        raise ValueError('resource missing or not marked unrestricted in directory')
    r = s.post(BASE + '/search', data={'query': query.strip(), 'queryType': 'cql', 'firstResultIndex': 1, 'numberOfResults': limit, 'resourceIds[]': resource_id}, timeout=30)
    r.raise_for_status()
    job = r.json()
    for _ in range(8):
        r = s.get(BASE + '/search/' + job, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data.get('inProgress'):
            break
        time.sleep(1)
    rows = []
    for x in data.get('results', []):
        rows.append({'resource': x.get('resource', {}).get('title'), 'resource_handle': x.get('resourceHandle'), 'endpoint': x.get('endpointUrl'), 'landing_page': x.get('resource', {}).get('landingPage'), 'availability_restriction': x.get('resource', {}).get('availabilityRestriction'), 'number_of_records': x.get('numberOfRecords'), 'diagnostics': x.get('diagnostics'), 'records': x.get('records', [])[:limit]})
    return {'source': 'CLARIN Federated Content Search', 'query': query, 'query_type': 'cql', 'in_progress': data.get('inProgress'), 'results': rows, 'note': 'Directory availability is not a license; check the source resource terms. Server may return more records than requested; output is capped.'}
