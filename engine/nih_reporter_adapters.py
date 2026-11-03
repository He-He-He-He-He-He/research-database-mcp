"""NIH RePORTER v2 project search, read-only despite its POST method."""
import release_runtime
import requests

def search(criteria, limit=10, offset=0):
    if not isinstance(criteria, dict) or not criteria:
        raise ValueError('criteria must be a non-empty object using NIH RePORTER fields')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('limit must be between 1 and 500')
    if not isinstance(offset, int) or isinstance(offset, bool) or (not 0 <= offset <= 14999):
        raise ValueError('offset must be between 0 and 14999')
    response = requests.post('https://api.reporter.nih.gov/v2/projects/search', json={'criteria': criteria, 'limit': limit, 'offset': offset}, timeout=30)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result.get('results'), list) or not isinstance(result.get('meta'), dict):
        raise RuntimeError('Unexpected NIH RePORTER response')
    return {'source': 'NIH RePORTER project API', 'meta': result['meta'], 'items': result['results'], 'note': 'Project award records; fiscal-year records can represent the same multi-year project.'}
