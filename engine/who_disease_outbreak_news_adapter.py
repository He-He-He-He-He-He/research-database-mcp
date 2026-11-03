"""WHO Disease Outbreak News OData, article metadata and detail."""
import release_runtime
import datetime, re
import requests
URL = 'https://www.who.int/api/emergencies/diseaseoutbreaknews'
PAGE = 'https://www.who.int/emergencies/disease-outbreak-news/'
SELECT = 'Title,PublicationDate,LastModified,UrlName,Summary,DonId'

def _get(params):
    with requests.get(URL, params=params, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 5000000:
                raise ValueError('Response too large')
        import json
        j = json.loads(raw)
        url = r.url
    if not isinstance(j.get('value'), list):
        raise ValueError('Unexpected WHO response')
    return (j, url)

def search(keyword='', start='', end='', limit=10, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((ord(x) < 32 for x in keyword)) or (type(limit) is not int) or (not 1 <= limit <= 50) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('Invalid query or pagination')
    for d in (start, end):
        if d:
            if not isinstance(d, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', d):
                raise ValueError('Dates must be YYYY-MM-DD')
            datetime.date.fromisoformat(d)
    if start and end and (start > end):
        raise ValueError('Invalid dates')
    if start or end:
        raise ValueError('WHO PublicationDate filtering has known historic coverage problems and is disabled')
    filters = []
    if keyword.strip():
        filters.append("contains(tolower(Title),'" + keyword.strip().lower().replace("'", "''") + "')")
    if start:
        filters.append('PublicationDate ge ' + start + 'T00:00:00Z')
    if end:
        filters.append('PublicationDate lt ' + (datetime.date.fromisoformat(end) + datetime.timedelta(days=1)).isoformat() + 'T00:00:00Z')
    p = {'$top': limit, '$skip': offset, '$orderby': 'PublicationDate desc', '$count': 'true', '$select': SELECT}
    if filters:
        p['$filter'] = ' and '.join(filters)
    j, url = _get(p)
    return {'source': url, 'source_page': PAGE, 'matched_total': j.get('@odata.count'), 'offset': offset, 'returned': len(j['value']), 'records': j['value'], 'notes': ['WHO Disease Outbreak News is a selected set of acute public-health event reports, not a comprehensive outbreak registry or real-time case count.', 'Keyword filtering is by title only. PublicationDate is not necessarily the event date; LastModified is separate.', 'Historical API coverage and publication-date migration may be incomplete or inconsistent. An empty result does not prove no outbreaks or reports existed.', 'Counts and case descriptions in a report are time-specific and may later change.']}

def detail(slug):
    if not isinstance(slug, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', slug):
        raise ValueError('Invalid WHO article slug')
    j, url = _get({'$filter': "UrlName eq '" + slug + "'", '$top': 2})
    if len(j['value']) > 1:
        raise ValueError('WHO returned duplicate slug')
    return {'source': url, 'article_url': PAGE + 'item/' + slug, 'records': j['value'], 'notes': ['Article text may contain HTML. Reported figures are specific to dates in the article, not necessarily current or final.', 'WHO DON reports selected events; absence is not evidence of no outbreak.']}
