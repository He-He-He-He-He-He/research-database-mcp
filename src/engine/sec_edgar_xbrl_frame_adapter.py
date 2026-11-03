"""SEC EDGAR XBRL calendar frame: one selected fact per reporting entity."""
import release_runtime
import re
import requests
DOC = 'https://www.sec.gov/search-filings/edgar-application-programming-interfaces'

def frame(taxonomy, concept, unit, period, user_agent, limit=20, offset=0, cik=None):
    if taxonomy not in ('us-gaap', 'ifrs-full', 'dei', 'srt'):
        raise ValueError('unsupported taxonomy')
    if not isinstance(concept, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,99}', concept):
        raise ValueError('invalid concept')
    if not isinstance(unit, str) or not re.fullmatch('[A-Za-z0-9_-]{1,40}', unit):
        raise ValueError('invalid unit')
    if not isinstance(period, str) or not re.fullmatch('CY[0-9]{4}(?:Q[1-4]I?)?', period):
        raise ValueError('period must be CYyyyy, CYyyyyQn or CYyyyyQnI')
    if not isinstance(user_agent, str) or len(user_agent) > 200 or (not re.search('[^\\s@]+@[^\\s@]+\\.[^\\s@]+', user_agent)) or ('\n' in user_agent) or ('\r' in user_agent):
        raise ValueError('user_agent must identify client and contact email per SEC policy')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('invalid offset')
    if cik is not None and (not isinstance(cik, str) or not re.fullmatch('[0-9]{1,10}', cik) or int(cik) == 0):
        raise ValueError('invalid CIK')
    url = f'https://data.sec.gov/api/xbrl/frames/{taxonomy}/{concept}/{unit}/{period}.json'
    r = requests.get(url, headers={'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}, timeout=45)
    r.raise_for_status()
    if len(r.content) > 15000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    rows = d.get('data')
    if not isinstance(rows, list) or not all((isinstance(x, dict) for x in rows)):
        raise ValueError('Unexpected frame format')
    chosen = rows if cik is None else [x for x in rows if str(x.get('cik')) == str(int(cik))]
    return {'source_url': r.url, 'documentation': DOC, 'taxonomy': d.get('taxonomy'), 'tag': d.get('tag'), 'period': d.get('ccp'), 'unit': d.get('uom'), 'label': d.get('label'), 'description': d.get('description'), 'source_count': d.get('pts'), 'match_count': len(chosen), 'items': chosen[offset:offset + limit], 'note': 'One last-filed fact per reporting entity closest to calendar period; underlying reporting dates may differ. Local pagination follows source order and is not a stable snapshot.'}
