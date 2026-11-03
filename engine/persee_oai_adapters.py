"""Persée OAI-PMH public bibliographic metadata; no restricted full text."""
import release_runtime
import xml.etree.ElementTree as ET
import requests
_OAI = '{http://www.openarchives.org/OAI/2.0/}'
_DC = '{http://purl.org/dc/elements/1.1/}'

def _get(params):
    r = requests.get('https://oai.persee.fr/oai', params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    error = root.find(_OAI + 'error')
    if error is not None:
        raise RuntimeError('OAI-PMH ' + str(error.get('code')) + ': ' + (error.text or ''))
    return root

def _record(record):
    header = record.find(_OAI + 'header')
    metadata = {}
    for el in record.findall('.//' + _DC + '*'):
        metadata.setdefault(el.tag.split('}', 1)[-1], []).append(el.text or '')
    return {'identifier': header.findtext(_OAI + 'identifier'), 'datestamp': header.findtext(_OAI + 'datestamp'), 'deleted': header.get('status') == 'deleted', 'metadata': metadata}

def get_record(identifier):
    if not isinstance(identifier, str) or not identifier.startswith('oai:persee:'):
        raise ValueError('identifier must be a Persée OAI identifier')
    root = _get({'verb': 'GetRecord', 'identifier': identifier, 'metadataPrefix': 'oai_dc'})
    rec = root.find(_OAI + 'GetRecord/' + _OAI + 'record')
    if rec is None:
        raise RuntimeError('Missing record')
    return {'source': 'Persée OAI-PMH', 'record': _record(rec)}

def list_records(set_id=None, resumption_token=None):
    if (set_id is None) == (resumption_token is None):
        raise ValueError('specify exactly one of set_id or resumption_token')
    if set_id is not None:
        if not isinstance(set_id, str) or not set_id.startswith('persee:'):
            raise ValueError('set_id must be a Persée set')
        params = {'verb': 'ListRecords', 'set': set_id, 'metadataPrefix': 'oai_dc'}
    else:
        if not isinstance(resumption_token, str) or not resumption_token:
            raise ValueError('resumption_token must be a non-empty string')
        params = {'verb': 'ListRecords', 'resumptionToken': resumption_token}
    root = _get(params)
    parent = root.find(_OAI + 'ListRecords')
    if parent is None:
        raise RuntimeError('Missing ListRecords')
    return {'source': 'Persée OAI-PMH', 'items': [_record(r) for r in parent.findall(_OAI + 'record')], 'resumption_token': parent.findtext(_OAI + 'resumptionToken') or None, 'note': 'Public bibliographic metadata, not full text; records may include deleted entries.'}
