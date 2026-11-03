"""Official U.S. National Science Foundation award search."""
import release_runtime
import requests

def search(keyword, size=10, offset=1):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword must be non-empty')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 25):
        raise ValueError('size must be from 1 to 25')
    if not isinstance(offset, int) or isinstance(offset, bool) or (not 1 <= offset <= 3000):
        raise ValueError('offset must be from 1 to 3000')
    response = requests.get('https://api.nsf.gov/services/v1/awards.json', params={'keyword': keyword, 'rpp': size, 'offset': offset, 'printFields': 'id,title,awardeeName,startDate,expDate,fundsObligatedAmt,totalCount'}, timeout=30)
    response.raise_for_status()
    data = response.json().get('response')
    if not isinstance(data, dict):
        raise RuntimeError('Unexpected NSF response')
    awards = data.get('award', [])
    if not isinstance(awards, list):
        raise RuntimeError('Unexpected NSF award list')
    return {'source': 'NSF Award Search API', 'query': keyword, 'offset': offset, 'items': [{k: a.get(k) for k in ('id', 'title', 'awardeeName', 'startDate', 'expDate', 'fundsObligatedAmt')} for a in awards], 'note': 'Award data; maximum 3000 results. Refine larger searches.'}
