"""UNIDO official SDMX 3.0 catalogue, structures, and bounded data requests."""
import release_runtime
import json
import re
import requests
BASE = 'https://stat.unido.org/portal/sdmx/'
DOC = 'https://stat.unido.org/unido-statistics-portal-api'

def _get(path, media, params=None):
    with requests.get(BASE + path, params=params, headers={'Accept': media}, stream=True, timeout=(15, 40)) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 5000000:
                raise RuntimeError('UNIDO response exceeds 5 MB; narrow query')
            chunks.append(chunk)
    doc = json.loads(b''.join(chunks))
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        raise RuntimeError('Unexpected UNIDO SDMX response')
    return doc

def _flow(flow):
    if not isinstance(flow, str) or not re.fullmatch('[A-Z0-9_]{1,80}', flow):
        raise ValueError('Invalid UNIDO flow identifier')
    return flow

def flows():
    return {'documentation': DOC, 'payload': _get('dataflow/UNIDO/all/latest', 'application/vnd.sdmx.dataflow+json;version=2.0.0')}

def structure(flow):
    return {'documentation': DOC, 'flow': _flow(flow), 'payload': _get('datastructure/UNIDO/' + flow + '_STRUCTURE/latest', 'application/vnd.sdmx.structure+json;version=2.0.0')}

def data(flow, key, start, end):
    _flow(flow)
    if not isinstance(key, str) or len(key) > 120 or (not re.fullmatch('\\d{3}(?:\\+\\d{3}){0,2}(?:\\.(?:[A-Z0-9_]+(?:\\+[A-Z0-9_]+)*|\\*)){0,3}', key)):
        raise ValueError('Invalid key: specify up to 3 numeric country codes and valid dimensions')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('\\d{4}', start)) or (not re.fullmatch('\\d{4}', end)) or (start > end):
        raise ValueError('Start/end must be ordered four-digit years')
    return {'documentation': DOC, 'request': {'flow': flow, 'key': key, 'startPeriod': start, 'endPeriod': end}, 'note': 'Raw UNIDO SDMX data; obtain flow structure, metadata and source documentation to interpret dimensions, units, currency and flags. Response may not include units. Max three countries; do not interpret empty results as zero.', 'payload': _get('data/UNIDO/' + flow + '/latest/' + key, 'application/vnd.sdmx.data+json;version=2.0.0', {'startPeriod': start, 'endPeriod': end})}
