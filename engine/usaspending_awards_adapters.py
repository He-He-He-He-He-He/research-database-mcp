"""Read-only US Treasury USAspending federal assistance award search."""
import release_runtime
from datetime import date
import requests

def search(keyword, start, end, page=1, limit=10):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword must be non-empty')
    try:
        a, b = (date.fromisoformat(start), date.fromisoformat(end))
        if a.isoformat() != start or b.isoformat() != end or b < a:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('start and end must be ordered YYYY-MM-DD') from None
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('page must be positive')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1 to 100')
    payload = {'filters': {'keywords': [keyword], 'award_type_codes': ['02', '03', '04', '05'], 'time_period': [{'start_date': start, 'end_date': end}]}, 'fields': ['Award ID', 'Recipient Name', 'Start Date', 'End Date', 'Award Amount', 'Awarding Agency', 'Award Type', 'Description'], 'page': page, 'limit': limit}
    r = requests.post('https://api.usaspending.gov/api/v2/search/spending_by_award/', json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('results'), list) or not isinstance(data.get('page_metadata'), dict):
        raise RuntimeError('Unexpected USAspending response')
    return {'source': 'US Treasury USAspending', 'keyword': keyword, 'start': start, 'end': end, 'items': data['results'], 'page_metadata': data['page_metadata'], 'messages': data.get('messages'), 'note': 'Federal assistance award records matching the API date filter, not all federal spending; by default start compares latest action date and end compares base transaction date. Award Amount is award-level obligation, not spending solely in the selected period.'}
