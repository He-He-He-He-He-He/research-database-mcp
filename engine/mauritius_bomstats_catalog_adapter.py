"""Read-only catalogue and dimensional structures of Bank of Mauritius BOMStats."""
import release_runtime
import json, re, subprocess
import requests
from urllib.parse import quote
BASE = 'https://bomstats.bom.mu/api/Core/'
MAX_BYTES = 8000000

def _get(path):
    proc = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('BOMStats request failed: ' + proc.stderr.decode('utf-8', 'replace')[:500])
    if len(proc.stdout) > MAX_BYTES:
        raise RuntimeError('response exceeds 8 MB')
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise RuntimeError('unexpected API response')
    return value

def search(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    raw = _get('nodes/7/catalog')
    datasets = raw.get('datasetMap')
    if not isinstance(datasets, dict):
        raise RuntimeError('unexpected catalogue')
    entries = []
    for identifier, details in datasets.items():
        if keyword.casefold() in (identifier + ' ' + str(details.get('title', '')) + ' ' + str(details.get('description', ''))).casefold():
            entries.append({'id': identifier, **details})
    return {'source': 'Bank of Mauritius BOMStats', 'source_url': 'https://bomstats.bom.mu/', 'keyword': keyword, 'total_datasets': len(datasets), 'matched': len(entries), 'items': entries, 'note': 'Catalogue metadata only, not statistical observations. Individual release terms and timing require verification.'}

def structure(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('MU2,[A-Za-z0-9_]{1,100},[0-9]+(?:\\.[0-9]+)*', identifier):
        raise ValueError('invalid dataset identifier')
    raw = _get('nodes/7/datasets/' + quote(identifier, safe=',') + '/structure')
    if not isinstance(raw.get('criteria'), list):
        raise RuntimeError('unexpected structure')
    return {'source': 'Bank of Mauritius BOMStats', 'id': identifier, 'structure': raw, 'note': 'Dimensions only; no numeric series queried or verified. Code lists, units and reuse terms require verification.'}

def latest(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('MU2,[A-Za-z0-9_]{1,100},[0-9]+(?:\\.[0-9]+)*', identifier):
        raise ValueError('invalid dataset identifier')
    if identifier not in {x['id'] for x in search()['items']}:
        raise ValueError('dataset not in current official catalogue')
    url = BASE + 'nodes/7/datasets/' + quote(identifier, safe=',') + '/data?lastNObservations=1'
    with requests.post(url, json=[], timeout=35, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.status_code != 200:
            raise RuntimeError('unexpected status')
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise RuntimeError('response exceeds 8 MB')
            chunks.append(chunk)
    raw = json.loads(b''.join(chunks))
    if raw.get('class') != 'dataset' or not isinstance(raw.get('dimension'), dict) or (not isinstance(raw.get('value'), (list, dict))):
        raise RuntimeError('unexpected JSON-stat response')
    return {'source': 'Bank of Mauritius BOMStats', 'id': identifier, 'url': url, 'data': raw, 'note': 'Unfiltered JSON-stat data with lastNObservations=1; inspect dimension codes, attributes, units, missing values and date. Latest period may not have observations for every series; no recalculation.'}
