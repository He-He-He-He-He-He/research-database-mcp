"""GovInfo public search API. DEMO_KEY is intended only for low-volume trials."""
import release_runtime
from urllib.parse import urlsplit
import requests
API = 'https://api.govinfo.gov'

def search(query, page_size=10, offset_mark='*', historical=False, api_key='DEMO_KEY'):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be nonempty')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 1000):
        raise ValueError('page_size must be between 1 and 1000')
    if not isinstance(historical, bool):
        raise ValueError('historical must be boolean')
    payload = {'query': query, 'pageSize': page_size, 'offsetMark': offset_mark, 'sorts': [{'field': 'score', 'sortOrder': 'DESC'}], 'historical': historical}
    r = requests.post(API + '/search', params={'api_key': api_key}, json=payload, timeout=40)
    r.raise_for_status()
    return r.json()

def read_link(url, api_key='DEMO_KEY'):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'api.govinfo.gov' or (not parsed.path.startswith('/packages/')) or parsed.query or parsed.fragment:
        raise ValueError('expected an unparameterized GovInfo package link')
    r = requests.get(url, params={'api_key': api_key}, timeout=40)
    r.raise_for_status()
    return {'content_type': r.headers.get('Content-Type'), 'content': r.content, 'source_url': url}
