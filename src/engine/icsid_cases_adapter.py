"""Official ICSID public case-database frontend data, filtered locally."""
import release_runtime
import requests
BASE = 'https://icsid.worldbank.org'
CASES = BASE + '/api/all/cases'
PAGE = BASE + '/cases/case-database'

def search(keyword='', respondent='', status='', offset=0, limit=20):
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be nonnegative')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    r = requests.get(CASES, timeout=60)
    r.raise_for_status()
    j = r.json()
    values = j.get('data', {}).get('GetAllCasesResult')
    if not isinstance(values, list):
        raise ValueError('unexpected case data')

    def match(row):
        if keyword and keyword.strip().casefold() not in ' '.join((str(row.get(k) or '') for k in ('caseno', 'casetitle', 'claimant', 'respondent', 'subject'))).casefold():
            return False
        if respondent and respondent.strip().casefold() not in str(row.get('respondent') or '').casefold():
            return False
        if status and status.strip().casefold() != str(row.get('status') or '').casefold():
            return False
        return True
    rows = [row for row in values if match(row)]
    return {'source': CASES, 'database': PAGE, 'download_bytes': len(r.content), 'total_cases': len(values), 'total_matches': len(rows), 'offset': offset, 'limit': limit, 'rows': rows[offset:offset + limit], 'notes': ['This is an official ICSID frontend data endpoint; server response is downloaded in full and filtered locally; endpoint stability is not assured.', 'Respondent and keyword are substring matches; a respondent may include multiple parties. Blank source fields are preserved and do not establish absence of decisions or events.', 'Case status and decisions are not judgments on the merits or proof of wrongdoing; documents may be unavailable or concern procedural steps.']}

def filters():
    url = BASE + '/api/all/filters'
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return {'source': url, 'data': r.json()}
