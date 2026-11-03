"""bioRxiv/medRxiv official preprint metadata by date interval."""
import release_runtime
from datetime import date
import requests

def search_dates(start_date, end_date, server='biorxiv', cursor=0, category=None):
    if server not in ('biorxiv', 'medrxiv'):
        raise ValueError('server must be biorxiv or medrxiv')
    try:
        start, end = (date.fromisoformat(start_date), date.fromisoformat(end_date))
    except (ValueError, TypeError):
        raise ValueError('dates must be YYYY-MM-DD') from None
    if start.isoformat() != start_date or end.isoformat() != end_date or end < start:
        raise ValueError('invalid date interval')
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 0:
        raise ValueError('cursor must be non-negative integer')
    if category is not None and (not isinstance(category, str) or not category.strip()):
        raise ValueError('category must be a non-empty string')
    url = f'https://api.biorxiv.org/details/{server}/{start_date}/{end_date}/{cursor}'
    response = requests.get(url, params={'category': category} if category else {}, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('messages'), list) or not isinstance(data.get('collection'), list):
        raise RuntimeError('Unexpected bioRxiv API response')
    if not data['messages'] or data['messages'][0].get('status') != 'ok':
        raise RuntimeError('bioRxiv API error: ' + str(data['messages']))
    return {'source': server, 'messages': data['messages'], 'items': data['collection'], 'note': 'Preprints may not be peer reviewed; returned counts include versions.'}
