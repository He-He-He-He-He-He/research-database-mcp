"""Look up bibliographic metadata by persistent IDs using OpenCitations Meta."""
import release_runtime
import os
from urllib.parse import quote
import requests

def lookup(identifiers):
    if not isinstance(identifiers, (list, tuple)) or not 1 <= len(identifiers) <= 10:
        raise ValueError('identifiers must be a list of 1 to 10 prefixed IDs')
    allowed = {'doi', 'issn', 'isbn', 'omid', 'openalex', 'pmid', 'pmcid'}
    for identifier in identifiers:
        if not isinstance(identifier, str) or ':' not in identifier or '__' in identifier:
            raise ValueError('each ID must contain a supported prefix and no double underscore')
        prefix, value = identifier.split(':', 1)
        if prefix not in allowed or not value.strip():
            raise ValueError('unsupported or empty identifier')
    headers = {'Accept': 'application/json'}
    if release_runtime.getenv('OPENCITATIONS_TOKEN'):
        headers['authorization'] = release_runtime.environment['OPENCITATIONS_TOKEN']
    path = '__'.join((quote(identifier, safe=':') for identifier in identifiers))
    r = requests.get('https://api.opencitations.net/meta/v1/metadata/' + path, headers=headers, timeout=30)
    r.raise_for_status()
    items = r.json()
    if not isinstance(items, list):
        raise RuntimeError('Unexpected OpenCitations Meta response')
    return {'source': 'OpenCitations Meta', 'identifiers': list(identifiers), 'items': items, 'note': 'Metadata for works indexed by OpenCitations; not an exhaustive search or full text.'}
