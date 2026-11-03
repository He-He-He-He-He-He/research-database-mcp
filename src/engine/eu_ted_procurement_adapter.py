"""EU TED public procurement notice search API."""
import release_runtime
import argparse, datetime, json, re
import requests
URL = 'https://api.ted.europa.eu/v3/notices/search'
FIELDS = ['publication-number', 'publication-date', 'notice-title', 'buyer-country', 'notice-type', 'contract-nature', 'classification-cpv']

def search(keyword, start=None, end=None, country=None, scope='ALL', page=1, limit=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((c in keyword for c in '"\\\r\n')):
        raise ValueError('invalid keyword')
    if scope not in ('ALL', 'ACTIVE') or not 1 <= limit <= 100 or page < 1 or (page * limit > 15000):
        raise ValueError('invalid scope or page')
    clauses = ['FT~' + json.dumps(keyword.strip(), ensure_ascii=False)]
    if country:
        if not re.fullmatch('[A-Z]{3}', country):
            raise ValueError('country must be a three-letter code')
        clauses.append('buyer-country=' + country)
    dates = []
    for d in (start, end):
        if d:
            try:
                dates.append(datetime.date.fromisoformat(d))
            except ValueError:
                raise ValueError('date must be YYYY-MM-DD') from None
        else:
            dates.append(None)
    if dates[0] and dates[1] and (dates[0] > dates[1]):
        raise ValueError('start exceeds end')
    if dates[0]:
        clauses.append('PD>=' + dates[0].strftime('%Y%m%d'))
    if dates[1]:
        clauses.append('PD<=' + dates[1].strftime('%Y%m%d'))
    query = ' AND '.join(clauses) + ' SORT BY publication-date DESC'
    body = {'query': query, 'fields': FIELDS, 'limit': limit, 'scope': scope, 'paginationMode': 'PAGE_NUMBER', 'page': page}
    with requests.post(URL, json=body, timeout=35, stream=True, headers={'Accept': 'application/json', 'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        data = json.loads(b''.join(parts))
    if not isinstance(data.get('notices'), list):
        raise ValueError('unexpected TED response')
    return {'source': URL, 'query': body, 'data': data}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--start')
    p.add_argument('--end')
    p.add_argument('--country')
    p.add_argument('--scope', choices=['ALL', 'ACTIVE'], default='ALL')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.start, a.end, a.country, a.scope, a.page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
