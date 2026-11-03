"""UK Parliament Bills public API, read-only queries."""
import release_runtime
import requests
BASE = 'https://bills-api.parliament.uk/api/v1/Bills'

def _get(path='', params=None):
    response = requests.get(BASE + path, params=params, timeout=35, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    response.raise_for_status()
    return response.json()

def _id(bill_id):
    if isinstance(bill_id, bool) or not isinstance(bill_id, int) or bill_id < 1:
        raise ValueError('bill_id must be a positive integer')
    return str(bill_id)

def search(query, skip=0, take=20):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be nonempty')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (skip, take))) or skip < 0 or (not 1 <= take <= 100):
        raise ValueError('skip must be nonnegative; take must be 1–100')
    return _get(params={'SearchTerm': query, 'Skip': skip, 'Take': take})

def bill(bill_id):
    return _get('/' + _id(bill_id))

def stages(bill_id, skip=0, take=20):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (skip, take))) or skip < 0 or (not 1 <= take <= 100):
        raise ValueError('invalid pagination')
    return _get('/' + _id(bill_id) + '/Stages', {'Skip': skip, 'Take': take})

def publications(bill_id):
    return _get('/' + _id(bill_id) + '/Publications')
