"""Library of Congress linked-data subject and name authority suggestions."""
import release_runtime
import requests

def search(query, kind='subjects'):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if kind not in ('subjects', 'names'):
        raise ValueError('kind must be subjects or names')
    r = requests.get('https://id.loc.gov/authorities/' + kind + '/suggest2/', params={'q': query}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('hits'), list) or 'count' not in data:
        raise RuntimeError('Unexpected LoC authority response')
    return {'source': 'Library of Congress Linked Data Service', 'kind': kind, 'query': query, 'total': data['count'], 'items': data['hits'], 'note': 'Left-anchored authority suggestions, first page only; not library holdings or full text.'}
