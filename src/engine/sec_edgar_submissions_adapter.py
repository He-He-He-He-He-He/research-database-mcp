"""SEC EDGAR recent submissions metadata for a specified CIK."""
import release_runtime
import re
import requests
DOC = 'https://www.sec.gov/search-filings/edgar-application-programming-interfaces'

def recent_filings(cik, user_agent, form=None, limit=10):
    if not isinstance(cik, str) or not re.fullmatch('[0-9]{1,10}', cik) or int(cik) == 0:
        raise ValueError('cik must be 1–10 digits')
    if not isinstance(user_agent, str) or len(user_agent) > 200 or (not re.search('[^\\s@]+@[^\\s@]+\\.[^\\s@]+', user_agent)) or ('\n' in user_agent) or ('\r' in user_agent):
        raise ValueError('user_agent must identify client and contact email per SEC policy')
    if form is not None and (not isinstance(form, str) or not re.fullmatch('[A-Za-z0-9 /-]{1,30}', form)):
        raise ValueError('invalid form')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    cik = cik.zfill(10)
    r = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json', headers={'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}, timeout=40)
    r.raise_for_status()
    if len(r.content) > 10000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    recent = d.get('filings', {}).get('recent', {})
    if not isinstance(recent, dict) or not isinstance(recent.get('form'), list):
        raise ValueError('Unexpected response format')
    columns = {k: v for k, v in recent.items() if isinstance(v, list)}
    n = len(recent['form'])
    if any((len(v) != n for v in columns.values())):
        raise ValueError('Inconsistent column lengths')
    items = []
    for idx in range(n):
        if form is not None and recent['form'][idx].upper() != form.upper():
            continue
        items.append({k: v[idx] for k, v in columns.items()})
        if len(items) >= limit:
            break
    return {'source_url': r.url, 'documentation': DOC, 'cik': cik, 'name': d.get('name'), 'tickers': d.get('tickers'), 'items': items, 'older_files_available': len(d.get('filings', {}).get('files', [])), 'note': 'Only SEC recent submissions array, not complete history or full filing text. SEC limits total automated traffic to 10 requests/second; callers must identify contact in User-Agent.'}
