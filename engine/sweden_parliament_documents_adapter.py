"""Official Swedish parliament document search and legislative status."""
import release_runtime
import json
import re
import requests
BASE = 'https://data.riksdagen.se/'
NOTES = ['Official Swedish Riksdag open parliamentary data include government bills (prop), members motions (mot), committee reports (bet) and other document types.', 'A proposal or committee report is not itself an enacted law. Even a law record may have later amendments or repeal; verify current legal text and effective dates from authoritative sources.', 'Keep publication, document, meeting and system update dates distinct. Current metadata and document versions do not prove what was available at an earlier cutoff.', 'Status response can contain large HTML text; it is omitted by default with an explicit flag, while metadata and procedural events remain.']

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=45, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('response exceeds 10 MB')
    j = json.loads(raw)
    if not isinstance(j, dict):
        raise ValueError('Unexpected Riksdag response')
    return j

def search(query, doctype=None, page=1, limit=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 150 or (doctype is not None and doctype not in ('prop', 'mot', 'bet', 'sfst')) or (type(page) is not int) or (not 1 <= page <= 10000) or (type(limit) is not int) or (not 1 <= limit <= 50):
        raise ValueError('Invalid document search')
    params = {'sok': query, 'utformat': 'json', 'p': page, 'sz': limit}
    if doctype:
        params['doktyp'] = doctype
    j = _get('dokumentlista/', params)
    d = j.get('dokumentlista')
    if not isinstance(d, dict) or '@traffar' not in d:
        raise ValueError('Unexpected document search')
    return {'source': BASE + 'dokumentlista/', 'query': query, 'document_type': doctype, 'notes': NOTES, 'response': d}

def status(docid, include_html=False):
    if not isinstance(docid, str) or not re.fullmatch('[A-Za-z0-9]{3,40}', docid) or type(include_html) is not bool:
        raise ValueError('Invalid document ID')
    url = 'dokumentstatus/' + docid + '.json'
    j = _get(url)
    d = j.get('dokumentstatus')
    if not isinstance(d, dict) or not isinstance(d.get('dokument'), dict) or str(d['dokument'].get('dok_id', '')).lower() != docid.lower():
        raise ValueError('Unexpected or unmatched document status')
    omitted = not include_html and 'html' in d['dokument']
    if omitted:
        d['dokument'].pop('html')
    return {'source': BASE + url, 'html_omitted': omitted, 'notes': NOTES, 'response': d}
