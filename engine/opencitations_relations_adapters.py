"""Small OpenCitations relation sets via official Index v2 API."""
import release_runtime
import os
from urllib.parse import quote
import requests
from opencitations_adapters import counts

def relations(identifier, direction='references', max_relations=100):
    if direction not in ('references', 'citations'):
        raise ValueError('direction must be references or citations')
    if not isinstance(max_relations, int) or isinstance(max_relations, bool) or (not 1 <= max_relations <= 100):
        raise ValueError('max_relations must be between 1 and 100')
    count = counts(identifier, 'reference' if direction == 'references' else 'citation')['count']
    if count > max_relations:
        raise ValueError('Too many relations for this endpoint; use the count or official data dump')
    headers = {'Accept': 'application/json'}
    if release_runtime.getenv('OPENCITATIONS_TOKEN'):
        headers['authorization'] = release_runtime.environment['OPENCITATIONS_TOKEN']
    r = requests.get('https://api.opencitations.net/index/v2/' + direction + '/' + quote(identifier, safe=':'), headers=headers, timeout=30)
    r.raise_for_status()
    items = r.json()
    if not isinstance(items, list):
        raise RuntimeError('Unexpected OpenCitations response')
    return {'source': 'OpenCitations Index', 'identifier': identifier, 'direction': direction, 'count_at_check': count, 'items': items, 'note': 'Only indexed relations; data may change between count and list requests.'}
