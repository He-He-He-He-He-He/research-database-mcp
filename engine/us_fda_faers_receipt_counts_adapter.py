"""openFDA FAERS daily report counts by FDA receipt date."""
import release_runtime
import datetime, re
import requests
URL = 'https://api.fda.gov/drug/event.json'
DOC = 'https://open.fda.gov/apis/drug/event/'

def _date(s):
    if not isinstance(s, str) or not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', s):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        raise ValueError('invalid date') from None

def daily_counts(start, end):
    a, b = (_date(start), _date(end))
    if a > b or (b - a).days > 30:
        raise ValueError('Date range must be ordered and at most 31 days')
    params = {'search': f'receiptdate:[{a:%Y%m%d} TO {b:%Y%m%d}]', 'count': 'receiptdate'}
    r = requests.get(URL, params=params, timeout=30)
    if r.status_code == 404:
        d = r.json()
        if d.get('error', {}).get('code') == 'NOT_FOUND':
            return {'source_url': r.url, 'data': {'results': []}, 'note': 'No records returned; not proof of no events or safety.'}
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    rows = d.get('results')
    if not isinstance(rows, list) or any((not isinstance(x, dict) or not isinstance(x.get('time'), str) or (not isinstance(x.get('count'), int)) for x in rows)):
        raise ValueError('Unexpected FAERS response')
    return {'source_url': r.url, 'documentation': DOC, 'data': d, 'note': 'Counts of submitted adverse-event reports by FDA receipt date; not incidence, unique patients, drug-attributable events, or causal proof. Data may lag and be revised; not medical advice.'}
