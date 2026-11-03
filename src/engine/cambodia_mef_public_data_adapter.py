"""Cambodian Ministry of Economy and Finance public dataset JSON API."""
import release_runtime
import re
import requests
BASE = 'https://data.mef.gov.kh/'
NOTES = ['Data for Economy and Finance portal aggregates data from different Cambodian public institutions; inspect the individual dataset page for publisher, coverage, definitions, licensing and update date.', 'Population dataset pd_6850e6071b4d5f000166ac2e labels its values as estimated population in millions; its 2024 value comes from an intercensal survey, not a complete census.', 'Current datasets may be revised. Observation years and catalogue creation dates do not establish a historical snapshot or when each value became available.', 'Raw API values and pagination are retained. Dataset page URLs are for source verification, not automatically fetched.']

def records(dataset, page=1, page_size=10):
    if not isinstance(dataset, str) or not re.fullmatch('pd_[a-f0-9]{24}', dataset) or type(page) is not int or (not 1 <= page <= 10000) or (type(page_size) is not int) or (not 1 <= page_size <= 100):
        raise ValueError('Invalid dataset ID or pagination')
    url = BASE + 'api/v1/public-datasets/' + dataset + '/json'
    with requests.get(url, params={'page': page, 'page_size': page_size}, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('response too large')
    import json
    j = json.loads(raw)
    if not isinstance(j, dict) or not isinstance(j.get('items'), list) or j.get('page') != page:
        raise ValueError('Unexpected dataset response')
    return {'source': url, 'dataset_page': BASE + 'datasets/' + dataset, 'notes': NOTES, 'response': j}
