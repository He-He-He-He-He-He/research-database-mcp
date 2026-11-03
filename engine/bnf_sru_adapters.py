"""French National Library public SRU catalogue search, Dublin Core metadata."""
import release_runtime
import requests
import xml.etree.ElementTree as ET

def search(query, size=10, start=1):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty SRU CQL')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be between 1 and 100')
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise ValueError('start must be a positive integer')
    r = requests.get('https://catalogue.bnf.fr/api/SRU', params={'version': '1.2', 'operation': 'searchRetrieve', 'query': query, 'recordSchema': 'dublincore', 'maximumRecords': size, 'startRecord': start}, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {'s': 'http://www.loc.gov/zing/srw/', 'dc': 'http://purl.org/dc/elements/1.1/'}
    count = root.findtext('s:numberOfRecords', namespaces=ns)
    if count is None:
        raise RuntimeError('BnF SRU did not return a result count: ' + ''.join(root.itertext())[:500])
    items = []
    for record in root.findall('s:records/s:record', ns):
        fields = {}
        for field in record.findall('.//{http://purl.org/dc/elements/1.1/}*'):
            fields.setdefault(field.tag.rsplit('}', 1)[-1], []).append(field.text or '')
        items.append(fields)
    return {'source': 'Bibliothèque nationale de France SRU', 'query': query, 'total': int(count), 'start': start, 'items': items, 'note': 'Bibliographic metadata only; not full-text access.'}
