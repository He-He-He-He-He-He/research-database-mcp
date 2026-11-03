"""Historical FDA food enforcement recall reports (not a safety-alert service)."""
import release_runtime
import os
import requests

def search(query, limit=10, skip=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty openFDA search syntax')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1 to 100')
    if not isinstance(skip, int) or isinstance(skip, bool) or (not 0 <= skip <= 25000):
        raise ValueError('skip must be 0 to 25000')
    params = {'search': query, 'limit': limit, 'skip': skip}
    if release_runtime.getenv('OPENFDA_API_KEY'):
        params['api_key'] = release_runtime.environment['OPENFDA_API_KEY']
    try:
        r = requests.get('https://api.fda.gov/food/enforcement.json', params=params, timeout=30)
    except requests.RequestException:
        raise RuntimeError('openFDA request failed') from None
    if not r.ok:
        raise RuntimeError(f'openFDA returned HTTP {r.status_code}')
    data = r.json()
    if not isinstance(data.get('results'), list):
        raise RuntimeError('Unexpected openFDA response')
    return {'source': 'FDA Recall Enterprise System via openFDA', 'meta': data.get('meta'), 'items': data['results'], 'note': 'Historical enforcement reports, not a live safety alert or full recall lifecycle. Data may be corrected; consult FDA notices.'}
