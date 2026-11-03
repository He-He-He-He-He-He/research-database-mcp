"""Portugal government open-data discovery with INE indicator code hints."""
import release_runtime
import json
import re
from urllib.parse import urlparse, parse_qs, quote
import requests
BASE = 'https://dados.gov.pt/api/1/datasets/'
NOTES = ['National open-data catalogue aggregates many publishers; inspect each publisher, licence, coverage, reference period and source independently.', 'Catalogue creation, modification, dataset observation and original publication dates are distinct; current entries do not prove a historical snapshot.', 'INE indicator codes below are extracted from official ine.pt resource URLs, not proof that any data values or historical vintages have been retrieved.', 'Listed resource URLs are returned as metadata only and are not fetched by this adapter.']

def _get(url, params=None):
    with requests.get(url, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('response too large')
    j = json.loads(raw)
    if not isinstance(j, dict):
        raise ValueError('Unexpected response')
    return j

def _codes(d):
    codes = set()
    for res in d.get('resources', []):
        p = urlparse(res.get('url') or '')
        if p.scheme == 'https' and p.hostname == 'www.ine.pt' and (p.path in ('/ine/json_indicador/pindica.jsp', '/ine/json_indicador/pindicaMeta.jsp')):
            for v in parse_qs(p.query).get('varcd', []):
                if re.fullmatch('\\d{7}', v):
                    codes.add(v)
    return sorted(codes)

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or (type(page) is not int) or (not 1 <= page <= 10000) or (type(limit) is not int) or (not 1 <= limit <= 50):
        raise ValueError('Invalid search')
    j = _get(BASE, {'q': keyword, 'page': page, 'page_size': limit})
    if not isinstance(j.get('data'), list):
        raise ValueError('Unexpected catalogue')
    return {'source': BASE, 'keyword': keyword, 'notes': NOTES, 'ine_codes_by_dataset': {d.get('slug', ''): _codes(d) for d in j['data']}, 'response': j}

def metadata(slug):
    if not isinstance(slug, str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,250}', slug):
        raise ValueError('Invalid dataset slug')
    url = BASE + quote(slug, safe='') + '/'
    j = _get(url)
    if j.get('slug') != slug or not isinstance(j.get('resources'), list):
        raise ValueError('Unexpected dataset')
    return {'source': url, 'notes': NOTES, 'ine_indicator_codes': _codes(j), 'dataset': j}
