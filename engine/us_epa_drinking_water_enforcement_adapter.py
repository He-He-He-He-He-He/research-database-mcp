"""US EPA Envirofacts SDWIS violation/enforcement records for one water system."""
import release_runtime
import json
import re
import requests
BASE = 'https://data.epa.gov/efservice/SDW_VIOL_ENFORCEMENT/PWSID/'
DOC = 'https://www.epa.gov/enviro/download-additional-envirofacts-datasets'
MAX = 8000000

def _get(url):
    r = requests.get(url, timeout=25, stream=True)
    r.raise_for_status()
    parts = []
    size = 0
    for b in r.iter_content(65536):
        size += len(b)
        if size > MAX:
            raise ValueError('EPA response exceeds limit')
        parts.append(b)
    return json.loads(b''.join(parts))

def violations(pwsid):
    if not isinstance(pwsid, str) or not re.fullmatch('[A-Z]{2}[0-9]{7}', pwsid):
        raise ValueError('PWSID must be two uppercase letters and seven digits')
    url = BASE + pwsid + '/JSON'
    rows = _get(url)
    if not isinstance(rows, list):
        raise ValueError('unexpected EPA response')
    if any((not isinstance(r, dict) or r.get('pwsid') != pwsid for r in rows)):
        raise ValueError('out-of-filter response')
    return {'source': url, 'documentation': DOC, 'pwsid': pwsid, 'returned': len(rows), 'upstream_total_available': False, 'rows': rows, 'note': 'EPA SDWIS enforcement/violation records, not real-time water quality or proof of current compliance. Dates reflect monitoring and enforcement periods; a violation can have multiple actions and is not necessarily a unique incident. Missing/empty response is not proof of safety. API supplies no total here, completeness unverified; timeout is an error, not an empty result.'}
