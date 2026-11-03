"""UK Parliament Treaties API; records laid before Parliament."""
import release_runtime
import re
import requests
BASE = 'https://treaties-api.parliament.uk/api/Treaty'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    return r.json()

def search(query, skip=0, take=20):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be nonempty')
    if any((isinstance(n, bool) or not isinstance(n, int) for n in (skip, take))) or skip < 0 or (not 1 <= take <= 100):
        raise ValueError('invalid paging')
    return _get(params={'SearchText': query.strip(), 'Skip': skip, 'Take': take})

def _id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9]+', identifier):
        raise ValueError('invalid treaty id')
    return identifier

def treaty(identifier):
    return _get('/' + _id(identifier))

def business_items(identifier):
    return _get('/' + _id(identifier) + '/BusinessItems')
