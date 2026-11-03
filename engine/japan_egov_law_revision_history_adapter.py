"""e-Gov Law API v2: revisions and article as of a specific date."""
import release_runtime
import datetime, re
import requests
BASE = 'https://laws.e-gov.go.jp/api/2'
DOC = 'https://laws.e-gov.go.jp/api/2/swagger-ui'

def _law(law_id):
    if not isinstance(law_id, str) or not re.fullmatch('[0-9]{3}[A-Z]{2}[0-9]{10}', law_id):
        raise ValueError('law_id must be a valid e-Gov law ID')

def _date(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError('invalid date') from None

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Unexpected response size')
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get('law_info'), dict):
        raise ValueError('Unexpected e-Gov response')
    return (r.url, data)

def revisions(law_id, start, end):
    _law(law_id)
    a = _date(start)
    b = _date(end)
    if a > b or (b - a).days > 1827:
        raise ValueError('date interval must be ordered and at most five years')
    url, d = _get('/law_revisions/' + law_id, {'amendment_date_from': start, 'amendment_date_to': end})
    if d['law_info'].get('law_id') != law_id or not isinstance(d.get('revisions'), list):
        raise ValueError('Unexpected revisions response')
    return {'source_url': url, 'documentation': DOC, 'data': d, 'note': 'Filter is amendment enforcement date; record status and notes are source-specific. This is not Westlaw Japan or legal advice.'}

def article_asof(law_id, article_number, asof):
    _law(law_id)
    _date(asof)
    if isinstance(article_number, bool) or not isinstance(article_number, int) or (not 1 <= article_number <= 9999):
        raise ValueError('article_number must be 1–9999')
    url, d = _get('/law_data/' + law_id, {'elm': f'Article_{article_number}', 'asof': asof, 'response_format': 'json', 'json_format': 'light'})
    if d['law_info'].get('law_id') != law_id or not isinstance(d.get('revision_info'), dict) or 'law_full_text' not in d:
        raise ValueError('Unexpected article response')
    return {'source_url': url, 'documentation': DOC, 'asof': asof, 'data': d, 'note': 'Source JSON law text is experimental. Check revision date and official gazette; propagation may lag. Only integer article numbers supported.'}
