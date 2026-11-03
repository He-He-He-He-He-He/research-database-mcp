"""Europe PMC first-page citation and reference links for one publication."""
import release_runtime
import re
import requests

def relations(identifier, source='MED', direction='citations', size=10):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_.-]+', identifier):
        raise ValueError('identifier must be a Europe PMC source ID')
    if source not in ('MED', 'PMC', 'PPR', 'AGR', 'CBA', 'CTX', 'ETH', 'HIR', 'NBK', 'PAT'):
        raise ValueError('unsupported Europe PMC source')
    if direction not in ('citations', 'references'):
        raise ValueError('direction must be citations or references')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be between 1 and 100')
    r = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{identifier}/{direction}', params={'format': 'json', 'pageSize': size}, timeout=30)
    r.raise_for_status()
    data = r.json()
    container, key = ('citationList', 'citation') if direction == 'citations' else ('referenceList', 'reference')
    request = data.get('request') if isinstance(data, dict) else None
    total = data.get('hitCount') if isinstance(data, dict) else None
    group = data.get(container) if isinstance(data, dict) else None
    items = group.get(key) if isinstance(group, dict) else [] if group is None else None
    if not isinstance(request, dict) or request.get('id') != identifier or request.get('source') != source or (request.get('offSet') != 1) or (request.get('pageSize') != size) or (type(total) is not int) or (total < 0) or (not isinstance(items, list)) or (len(items) > min(size, total)) or (total > 0 and (not items)) or any((not isinstance(item, dict) for item in items)):
        raise RuntimeError('Unexpected Europe PMC response, identity or page')
    return {'source': 'Europe PMC', 'id': identifier, 'id_source': source, 'direction': direction, 'total': total, 'items': items, 'note': 'First page only; links reflect Europe PMC indexed coverage.'}
