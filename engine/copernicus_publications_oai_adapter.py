"""Copernicus Publications official OAI-PMH: metadata only, low-volume manual paging."""
import release_runtime
import re, json, subprocess, urllib.parse, xml.etree.ElementTree as ET
from datetime import date
BASE = 'https://oai-pmh.copernicus.org/oai.php'
O = '{http://www.openarchives.org/OAI/2.0/}'
DC = '{http://purl.org/dc/elements/1.1/}'

def _request(params):
    url = BASE + '?' + urllib.parse.urlencode(params)
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Copernicus request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    root = ET.fromstring(p.stdout)
    errors = root.findall(O + 'error')
    if errors:
        if all((e.get('code') == 'noRecordsMatch' for e in errors)):
            return root
        raise RuntimeError('OAI-PMH: ' + '; '.join(((e.get('code') or '') + ': ' + (e.text or '') for e in errors)))
    return root

def _parse_records(root):
    entries = []
    for r in root.findall('.//' + O + 'record'):
        header = r.find(O + 'header')
        meta = r.find(O + 'metadata')
        fields = {}
        if meta is not None:
            for el in meta.iter():
                if el.tag.startswith(DC):
                    fields.setdefault(el.tag[len(DC):], []).append((el.text or '').strip())
        entries.append({'identifier': header.findtext(O + 'identifier') if header is not None else None, 'datestamp': header.findtext(O + 'datestamp') if header is not None else None, 'status': header.get('status') if header is not None else None, 'sets': [x.text for x in header.findall(O + 'setSpec')] if header is not None else [], 'metadata': fields})
    token = root.find('.//' + O + 'resumptionToken')
    return {'records': entries, 'resumption_token': token.text if token is not None else None, 'cursor': token.get('cursor') if token is not None else None, 'complete_list_size': token.get('completeListSize') if token is not None else None, 'note': '仅公开 OAI 元数据；不支持关键词检索，全文与具体许可须单独核实。datestamp 不是出版日期；上游窄日期查询曾与单条记录日期矛盾，空结果不能证明无数据。'}

def sets():
    root = _request({'verb': 'ListSets'})
    return [{'id': s.findtext(O + 'setSpec'), 'name': s.findtext(O + 'setName')} for s in root.findall('.//' + O + 'set')]

def get(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('oai:publications\\.copernicus\\.org:[a-z0-9]{1,40}', identifier):
        raise ValueError('Invalid Copernicus OAI identifier')
    return _parse_records(_request({'verb': 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': identifier}))

def records(set_id, since, until):
    if not isinstance(set_id, str) or not re.fullmatch('[A-Za-z0-9_-]{1,40}', set_id):
        raise ValueError('Invalid set')
    a, b = (date.fromisoformat(since), date.fromisoformat(until))
    if a > b:
        raise ValueError('Invalid date range')
    return _parse_records(_request({'verb': 'ListRecords', 'metadataPrefix': 'oai_dc', 'set': set_id, 'from': str(a), 'until': str(b)}))

def next_page(token):
    if not isinstance(token, str) or not token or len(token) > 2000 or any((ord(c) < 32 for c in token)):
        raise ValueError('Invalid token')
    return _parse_records(_request({'verb': 'ListRecords', 'resumptionToken': token}))
