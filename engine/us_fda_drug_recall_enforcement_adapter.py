"""openFDA drug recall enforcement reports by classification and report dates."""
import release_runtime
import datetime, re
import requests
URL = 'https://api.fda.gov/drug/enforcement.json'
DOC = 'https://open.fda.gov/apis/drug/enforcement/'

def _date(s):
    if not isinstance(s, str) or not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', s):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        raise ValueError('invalid date') from None

def reports(classification, start, end, limit=10, skip=0):
    if classification not in ('I', 'II', 'III'):
        raise ValueError('classification must be I, II, or III')
    a, b = (_date(start), _date(end))
    if a > b or (b - a).days > 366:
        raise ValueError('Date interval must be ordered and at most 366 days')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(skip, bool) or not isinstance(skip, int) or (not 0 <= skip <= 25000):
        raise ValueError('skip out of range')
    q = f'classification:"Class {classification}" AND report_date:[{a:%Y%m%d} TO {b:%Y%m%d}]'
    r = requests.get(URL, params={'search': q, 'limit': limit, 'skip': skip, 'sort': 'report_date:desc'}, timeout=30)
    if r.status_code == 404:
        payload = r.json()
        if payload.get('error', {}).get('code') == 'NOT_FOUND':
            return {'source_url': r.url, 'data': {'results': []}, 'note': 'No FDA results for query; does not establish safety.'}
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    if not isinstance(d.get('results'), list) or not isinstance(d.get('meta', {}).get('results', {}).get('total'), int):
        raise ValueError('Unexpected openFDA response')
    return {'source_url': r.url, 'documentation': DOC, 'data': d, 'note': 'FDA recall enforcement records; report date is not necessarily initiation date. Results are not clinical guidance, and absence does not establish safety.'}
