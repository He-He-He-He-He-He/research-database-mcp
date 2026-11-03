"""OpenCitations Index v2 counts for identified scholarly works."""
import release_runtime
import os
from urllib.parse import quote
import requests

def counts(identifier, direction='citation'):
    if not isinstance(identifier, str) or ':' not in identifier:
        raise ValueError('identifier must have type prefix, such as doi:10.1234/example')
    prefix, value = identifier.split(':', 1)
    if prefix not in ('doi', 'pmid', 'issn', 'isbn', 'omid') or not value.strip():
        raise ValueError('supported identifiers: doi, pmid, issn, isbn, omid')
    if direction not in ('citation', 'reference'):
        raise ValueError('direction must be citation or reference')
    headers = {'Accept': 'application/json'}
    if release_runtime.getenv('OPENCITATIONS_TOKEN'):
        headers['authorization'] = release_runtime.environment['OPENCITATIONS_TOKEN']
    url = 'https://api.opencitations.net/index/v2/' + direction + '-count/' + quote(identifier, safe=':')
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or len(rows) != 1 or 'count' not in rows[0]:
        raise RuntimeError('Unexpected OpenCitations count response')
    return {'source': 'OpenCitations Index', 'identifier': identifier, 'direction': direction, 'count': int(rows[0]['count']), 'note': 'Only citations indexed by OpenCitations, not all scholarly citations.'}
