"""INSEE Melodi public catalogue, dataset metadata and filtered observations.

Values retain their original dimensions, measure names and statuses. Dataset
metadata and codes must be read before interpreting geographic scope, units,
estimation and time reference. Anonymous API limit: 30 requests/minute.
"""
import release_runtime
import re
import requests
BASE = 'https://api.insee.fr/melodi/'

def _dataset(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Z][A-Z0-9_]{1,100}', value):
        raise ValueError('invalid INSEE dataset ID')
    return value

def _get(path, params=None):
    response = requests.get(BASE + path, params=params, timeout=45)
    response.raise_for_status()
    return response.json()

def catalogue(query=''):
    result = _get('catalog/all')
    if not isinstance(result, list):
        raise ValueError('unexpected catalogue response')
    return [x for x in result if query.casefold() in str(x).casefold()]

def metadata(dataset):
    return _get('catalog/' + _dataset(dataset))

def observations(dataset, filters, page=1):
    """Fetch a single page using dimension filters from dataset metadata.

    Use the returned paging links to discover whether further pages exist.
    Supplying a restrictive geography or other dimension avoids huge queries.
    """
    if not isinstance(filters, dict) or not filters:
        raise ValueError('at least one filter is required')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page must be positive')
    for k, v in filters.items():
        if not isinstance(k, str) or not re.fullmatch('[A-Z][A-Z0-9_]*', k):
            raise ValueError('invalid dimension')
        if not isinstance(v, str) or not v or len(v) > 200:
            raise ValueError('invalid dimension value')
    return _get('data/' + _dataset(dataset), {**filters, 'page': page})
