"""French education ministry open dataset catalog and record API."""
import release_runtime
import re
import requests
BASE = 'https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets'
NOTES = ['French education ministry open-data platform includes multiple education, sports and youth datasets. Verify the publisher, coverage, observation date, update frequency and licence for each dataset.', 'The national education directory describes establishments according to the source metadata; counts represent matching records and are not automatically counts of unique schools.', 'Current datasets may be updated or revised. A current record with an old observation date does not prove historical publication or historical state.', 'Raw source fields, nulls, and total_count are preserved. Results are paginated and may change between requests.']

def _get(url, params=None):
    with requests.get(url, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('response exceeds size limit')
    import json
    j = json.loads(raw)
    if not isinstance(j, dict) or 'error_code' in j:
        raise ValueError('Unexpected education API response')
    return j

def _url(dataset):
    if not isinstance(dataset, str) or not re.fullmatch('[a-z0-9][a-z0-9_-]{0,150}', dataset):
        raise ValueError('Invalid dataset identifier')
    return BASE + '/' + dataset

def _page(limit, offset):
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('Invalid pagination')

def catalog(limit=10, offset=0):
    _page(limit, offset)
    j = _get(BASE, {'limit': limit, 'offset': offset})
    if not isinstance(j.get('results'), list):
        raise ValueError('Unexpected catalogue')
    return {'source': BASE, 'notes': NOTES, 'response': j}

def metadata(dataset):
    url = _url(dataset)
    j = _get(url)
    if j.get('dataset_id') != dataset or not isinstance(j.get('fields'), list):
        raise ValueError('Unexpected metadata')
    return {'source': url, 'notes': NOTES, 'dataset': j}

def records(dataset, limit=10, offset=0, field=None, value=None):
    _page(limit, offset)
    url = _url(dataset)
    meta = metadata(dataset)['dataset']
    params = {'limit': limit, 'offset': offset}
    if field is not None or value is not None:
        valid = {f['name'] for f in meta['fields'] if f.get('type') == 'text' and isinstance(f.get('name'), str)}
        if field not in valid or not isinstance(value, str) or (not re.fullmatch('[\\w \\-]{1,100}', value)):
            raise ValueError('Filter must use a text field and a simple exact value')
        params['where'] = field + " = '" + value + "'"
    j = _get(url + '/records', params)
    if not isinstance(j.get('results'), list):
        raise ValueError('Unexpected records')
    return {'source': url + '/records', 'notes': NOTES, 'dataset_metadata': meta, 'filter': {'field': field, 'value': value} if field else None, 'response': j}
