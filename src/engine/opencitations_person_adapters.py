"""OpenCitations Meta works linked to an author or editor ORCID."""
import release_runtime
import os
import re
import requests

def works(orcid, role='author'):
    if not isinstance(orcid, str) or not re.fullmatch('\\d{4}-\\d{4}-\\d{4}-\\d{3}[\\dX]', orcid):
        raise ValueError('orcid must be formatted 0000-0000-0000-0000')
    if role not in ('author', 'editor'):
        raise ValueError('role must be author or editor')
    headers = {'Accept': 'application/json'}
    if release_runtime.getenv('OPENCITATIONS_TOKEN'):
        headers['authorization'] = release_runtime.environment['OPENCITATIONS_TOKEN']
    response = requests.get('https://api.opencitations.net/meta/v1/' + role + '/orcid:' + orcid, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError('Unexpected OpenCitations Meta response')
    return {'source': 'OpenCitations Meta', 'orcid': orcid, 'role': role, 'items': data, 'note': 'Only indexed associations, not a complete verified publication list.'}
