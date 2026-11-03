"""Lookup SEC's public ticker/exchange/CIK mapping by ticker or company name."""
import release_runtime
import re
import requests
URL = 'https://www.sec.gov/files/company_tickers_exchange.json'
DOC = 'https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data'

def find_company(query, user_agent, mode='ticker', limit=20):
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 100 or any((ord(c) < 32 for c in query)):
        raise ValueError('query must contain 2–100 characters')
    if mode not in ('ticker', 'name'):
        raise ValueError('mode must be ticker or name')
    if not isinstance(user_agent, str) or len(user_agent) > 200 or (not re.search('[^\\s@]+@[^\\s@]+\\.[^\\s@]+', user_agent)) or ('\n' in user_agent) or ('\r' in user_agent):
        raise ValueError('user_agent must identify client and contact email per SEC policy')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    r = requests.get(URL, headers={'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}, timeout=40)
    r.raise_for_status()
    if len(r.content) > 10000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    fields = d.get('fields')
    rows = d.get('data')
    if fields != ['cik', 'name', 'ticker', 'exchange'] or not isinstance(rows, list) or any((not isinstance(row, list) or len(row) != 4 for row in rows)):
        raise ValueError('Unexpected SEC index shape')
    q = query.strip().casefold()
    matched = []
    for row in rows:
        value = str(row[2] if mode == 'ticker' else row[1]).casefold()
        if value == q if mode == 'ticker' else q in value:
            matched.append(dict(zip(fields, row)))
    return {'source_url': r.url, 'documentation': DOC, 'query': query, 'mode': mode, 'match_count': len(matched), 'items': matched[:limit], 'note': 'SEC ticker/exchange mapping is not a complete directory of all EDGAR filers; verify CIK and entity identity before interpreting filings.'}
