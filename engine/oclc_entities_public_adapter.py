"""OCLC WorldCat Entities anonymous known-ID detail; not WorldCat Search or holdings."""
import release_runtime
import re
import requests
BASE = 'https://id.oclc.org/worldcat/entity/'

def entity_detail(entity_id, timeout=20):
    """Get the publicly available JSON-LD properties of one known entity ID."""
    if not isinstance(entity_id, str) or not re.fullmatch('E39[A-Za-z0-9]{23}', entity_id):
        raise ValueError('Expected a WorldCat entity identifier, e.g. E39PBJymGv6xMdcX3dQdb48KVC')
    url = BASE + entity_id + '.jsonld'
    response = requests.get(url, headers={'Accept': 'application/ld+json'}, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if data.get('id') != BASE + entity_id:
        raise ValueError('Unexpected entity identifier in response')
    return {'source': 'OCLC WorldCat Entities (anonymous)', 'source_url': url, 'scope': 'Known entity detail only; limited anonymous properties, no catalog search or holdings', 'data': data}
