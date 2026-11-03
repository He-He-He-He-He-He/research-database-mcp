"""ORCID anonymous public registry search, read-only.

ORCID IDs found by search are candidates, not authenticated identities.
https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/
"""
import release_runtime
import requests

def search(query, start=0, rows=10):
    """Search public profiles using ORCID's Solr query syntax."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(start, int) or isinstance(start, bool) or start < 0:
        raise ValueError('start must be a non-negative integer')
    if not isinstance(rows, int) or isinstance(rows, bool) or (not 1 <= rows <= 100):
        raise ValueError('rows must be between 1 and 100')
    response = requests.get('https://pub.orcid.org/v3.0/expanded-search/', params={'q': query, 'start': start, 'rows': rows}, headers={'Accept': 'application/json'}, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('expanded-result'), list) or 'num-found' not in data:
        raise RuntimeError('Unexpected ORCID response')
    items = [{k: item.get(k) for k in ('orcid-id', 'given-names', 'family-names', 'credit-name', 'other-name', 'institution-name')} for item in data['expanded-result']]
    return {'source': 'ORCID public registry', 'query': query, 'start': start, 'total': data['num-found'], 'items': items, 'note': 'Public profiles only; name-search matches do not authenticate identity.'}
