"""Rijksmuseum official Linked Art search and persistent identifier resolver."""
import release_runtime
import re
from urllib.parse import urlparse, parse_qs
import requests
BASE = 'https://data.rijksmuseum.nl'
DOC = 'https://data.rijksmuseum.nl/docs/search'

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('Unexpected response size')
    return (r.url, r.json())

def search(value, field='creator', page_token=None):
    if field not in ('creator', 'title', 'type', 'material', 'description', 'objectNumber'):
        raise ValueError('Unsupported search field')
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise ValueError('value must be 1–100 characters')
    if page_token is not None and (not isinstance(page_token, str) or not re.fullmatch('[A-Za-z0-9_-]{1,2048}', page_token)):
        raise ValueError('Invalid page token')
    params = {field: value.strip()}
    if page_token:
        params['pageToken'] = page_token
    url, d = _get('/search/collection', params)
    if not isinstance(d, dict) or d.get('type') != 'OrderedCollectionPage' or (not isinstance(d.get('orderedItems'), list)):
        raise ValueError('Unexpected search response')
    nexturl = d.get('next', {}).get('id')
    nexttoken = None
    if nexturl:
        parsed = urlparse(nexturl)
        q = parse_qs(parsed.query)
        if parsed.scheme != 'https' or parsed.hostname != 'data.rijksmuseum.nl' or parsed.path != '/search/collection' or (q.get(field) != [value.strip()]) or (len(q.get('pageToken', [])) != 1):
            raise ValueError('Unexpected next-page URL')
        nexttoken = q['pageToken'][0]
    return {'source_url': url, 'documentation': DOC, 'data': d, 'next_page_token': nexttoken, 'note': 'Returns object identifiers, 100 per page; library and archive records excluded. Images require separate rights checks.'}

def object_detail(object_id):
    if isinstance(object_id, bool) or not isinstance(object_id, int) or (not 1 <= object_id <= 9999999999):
        raise ValueError('object_id must be a positive integer')
    url, d = _get('/' + str(object_id))
    if not isinstance(d, dict) or d.get('id') != 'https://id.rijksmuseum.nl/' + str(object_id):
        raise ValueError('Unexpected detail response')
    return {'source_url': url, 'documentation': 'https://data.rijksmuseum.nl/docs/http', 'data': d, 'note': 'Official Linked Art metadata; check rights and image conditions per object.'}
