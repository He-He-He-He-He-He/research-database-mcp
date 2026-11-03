"""Ecuador government open data CKAN search and bounded hosted CSV reader."""
import release_runtime
import csv
import hashlib
import io
import re
from urllib.parse import urlparse
import requests
BASE = 'https://www.datosabiertos.gob.ec/api/3/action/'
NOTES = ['The Ecuador government catalogue aggregates data from many institutions; publisher, dataset-specific licence, coverage and reference periods vary.', 'CSV values and duplicate column positions are retained as strings; consult the dataset dictionary for units, delimiters, encoding, missing values and geographic scope.', 'Resource availability and values can change. Publication/update timestamps do not by themselves establish an earlier historical snapshot.', 'CSV reading is limited to HTTPS files hosted directly on the official datosabiertos.gob.ec domain and at most 12 MB. Other resources remain discoverable but are not fetched by this reader.']

def _api(action, params):
    r = requests.get(BASE + action, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or j.get('success') is not True or 'result' not in j:
        raise ValueError('Ecuador CKAN API error')
    return j['result']

def search(keyword, limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid catalogue query')
    j = _api('package_search', {'q': keyword, 'rows': limit, 'start': offset})
    if not isinstance(j, dict) or type(j.get('count')) is not int or (not isinstance(j.get('results'), list)):
        raise ValueError('Unexpected CKAN search')
    return {'source': BASE + 'package_search', 'query': keyword, 'total_matching': j['count'], 'offset': offset, 'notes': NOTES, 'records': j['results']}

def metadata(dataset):
    if not isinstance(dataset, str) or not re.fullmatch('[a-zA-Z0-9_-]{1,120}', dataset):
        raise ValueError('Invalid dataset ID')
    j = _api('package_show', {'id': dataset})
    if not isinstance(j, dict) or not isinstance(j.get('resources'), list):
        raise ValueError('Unexpected CKAN metadata')
    return {'source': BASE + 'package_show', 'notes': NOTES, 'dataset': j}

def csv_records(resource_id, filters=None, encoding='utf-8-sig', delimiter=',', limit=20, offset=0):
    if not isinstance(resource_id, str) or not re.fullmatch('[a-fA-F0-9-]{36}', resource_id) or encoding not in ('utf-8-sig', 'latin-1', 'cp1252') or (delimiter not in (',', ';', '\t', '|')) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid CSV request')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > 5 or any((not isinstance(k, str) or not isinstance(v, str) or len(k) > 100 or (len(v) > 200) for k, v in filters.items())):
        raise ValueError('Invalid filters')
    resource = _api('resource_show', {'id': resource_id})
    if not isinstance(resource, dict) or str(resource.get('id', '')).lower() != resource_id.lower() or str(resource.get('format', '')).upper() != 'CSV':
        raise ValueError('Resource is not an identified CSV')
    u = resource.get('url', '')
    p = urlparse(u)
    if p.scheme != 'https' or p.hostname != 'www.datosabiertos.gob.ec' or (not p.path.startswith('/dataset/')):
        raise ValueError('Resource URL is not an official hosted CSV')
    with requests.get(u, timeout=60, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if 300 <= r.status_code < 400:
            raise ValueError('CSV redirect not accepted')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 12000000:
                raise ValueError('CSV exceeds 12 MB limit')
        modified = r.headers.get('Last-Modified')
    reader = csv.reader(io.StringIO(bytes(raw).decode(encoding), newline=''), delimiter=delimiter)
    headers = next(reader, None)
    if not headers or any((headers.count(k) != 1 for k in filters)):
        raise ValueError('Missing or ambiguous CSV filter column')
    indexes = {k: headers.index(k) for k in filters}
    rows = []
    total = 0
    for row in reader:
        if len(row) != len(headers):
            raise ValueError('Inconsistent CSV row width')
        if any((row[i] != filters[k] for k, i in indexes.items())):
            continue
        if offset <= total < offset + limit:
            rows.append(row)
        total += 1
    return {'source': u, 'resource': resource, 'http_last_modified': modified, 'sha256': hashlib.sha256(raw).hexdigest(), 'encoding': encoding, 'delimiter': delimiter, 'columns': headers, 'total_matching': total, 'offset': offset, 'notes': NOTES, 'records': rows}
