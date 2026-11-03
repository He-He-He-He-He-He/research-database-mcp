"""France DILA official association and mandatory financial notices."""
import release_runtime
import json
import re
import requests
BASE = 'https://journal-officiel-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/'
DATA = {'balo': 'balo', 'associations': 'jo_associations'}
NOTES = ['DILA official notices: BALO covers required financial disclosures for relevant issuers and financial institutions; JOAFE covers association and foundation notices and accounts.', 'A published notice is an event, not proof of current legal status, financial condition or an exhaustive company record. It is not a full legislative text database.', 'Publication date, effective date, correction and current status differ; inspect original notice and follow-up notices.', 'Preserve DILA attribution and source URL; verify reuse conditions and personal-data rules on the official dataset page. Current data may be revised and are not a historical snapshot.']

def _get(url, params=None):
    with requests.get(url, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 10000000:
                raise ValueError('response too large')
    j = json.loads(raw)
    if not isinstance(j, dict) or 'error_code' in j:
        raise ValueError('Unexpected DILA response')
    return j

def _url(kind):
    if kind not in DATA:
        raise ValueError('Invalid notice dataset')
    return BASE + DATA[kind]

def metadata(kind):
    u = _url(kind)
    j = _get(u)
    if j.get('dataset_id') != DATA[kind]:
        raise ValueError('Dataset mismatch')
    return {'source': u, 'notes': NOTES, 'metadata': j}

def records(kind, identifier=None, limit=10, offset=0):
    u = _url(kind)
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('Invalid pagination')
    params = {'limit': limit, 'offset': offset, 'order_by': 'dateparution DESC'}
    if identifier is not None:
        if not isinstance(identifier, str) or not re.fullmatch('\\d{9}' if kind == 'balo' else '[0-9A-Za-z]{2,3}', identifier):
            raise ValueError('Invalid SIREN or department code')
        params['where'] = ('siren' if kind == 'balo' else 'departement_code') + " = '" + identifier + "'"
    j = _get(u + '/records', params)
    if not isinstance(j.get('results'), list):
        raise ValueError('Unexpected notice records')
    return {'source': u + '/records', 'dataset': kind, 'identifier': identifier, 'notes': NOTES, 'response': j}
