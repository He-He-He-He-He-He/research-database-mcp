"""World Bank Documents & Reports official API metadata search."""
import release_runtime
import re
import requests
URL = 'https://search.worldbank.org/api/v3/wds'
DOC = 'https://documents.worldbank.org/en/publication/documents-reports/api'
FIELDS = 'id,display_title,docdt,pdfurl,url,docty,lang'

def _fetch(p):
    r = requests.get(URL, params=p, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or not isinstance(j.get('documents'), dict):
        raise ValueError('unexpected World Bank response')
    return {'source': URL, 'documentation': DOC, 'request': p, 'data': j, 'notes': ['Search covers the fields indexed by the World Bank, not only titles or full text; metadata matches should be reviewed individually.', 'Document date is source metadata and may differ from a report’s reference period or the events described.', 'PDF links, abstract and metadata are as provided. Search access does not establish unrestricted reuse, PDF availability or complete full-text coverage; verify each document’s rights and source.']}

def search(keyword, offset=0, limit=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 300:
        raise ValueError('keyword must be nonempty and at most 300 characters')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    result = _fetch({'format': 'json', 'qterm': keyword.strip(), 'rows': limit, 'os': offset, 'fl': FIELDS})
    data = result['data']
    docs = data['documents']
    items = [v for k, v in docs.items() if k != 'facets']
    if type(data.get('total')) is not int or data['total'] < 0 or data.get('rows') != limit or (data.get('os') != offset):
        raise ValueError('World Bank search paging metadata mismatch')
    if any((not isinstance(item, dict) for item in items)) or len(items) > min(limit, max(0, data['total'] - offset)):
        raise ValueError('World Bank document count contradicts paging metadata')
    return result

def detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('\\d{1,20}', identifier):
        raise ValueError('document identifier must be digits')
    data = _fetch({'format': 'json', 'id': identifier, 'fl': FIELDS})
    docs = data['data'].get('documents', {})
    if not any((isinstance(v, dict) and v.get('id') == identifier for v in docs.values())):
        raise ValueError('document not found')
    return data
