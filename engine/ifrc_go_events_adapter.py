"""IFRC GO publicly visible emergency event summaries."""
import release_runtime
import datetime
import requests
BASE = 'https://goadmin.ifrc.org/api/v2/'

def _get(path, params):
    with requests.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        body = r.raw.read(5000001, decode_content=True)
    if len(body) > 5000000:
        raise ValueError('response exceeds size limit')
    import json
    data = json.loads(body)
    if not isinstance(data.get('results'), list):
        raise ValueError('unexpected response')
    return data

def countries(*, offset=0, limit=50):
    if any((type(x) is not int for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('invalid pagination')
    d = _get('country/', {'offset': offset, 'limit': limit})
    return {'count': d['count'], 'next': d['next'], 'records': [{k: x.get(k) for k in ('id', 'name', 'iso', 'iso3', 'record_type_display')} for x in d['results']]}

def query(country_id, date_from, date_to, *, offset=0, limit=20):
    if type(country_id) is not int or country_id <= 0 or type(offset) is not int or (offset < 0) or (type(limit) is not int) or (not 1 <= limit <= 100):
        raise ValueError('invalid country ID or pagination')
    try:
        start = datetime.date.fromisoformat(date_from)
        end = datetime.date.fromisoformat(date_to)
    except (TypeError, ValueError):
        raise ValueError('dates must be YYYY-MM-DD')
    if start > end or (end - start).days > 366 * 10:
        raise ValueError('date range must be ordered and no longer than 10 years')
    p = {'countries__in': country_id, 'disaster_start_date__gte': date_from, 'disaster_start_date__lt': (end + datetime.timedelta(days=1)).isoformat(), 'offset': offset, 'limit': limit}
    d = _get('event/', p)
    out = []
    for event in d['results']:
        out.append({'id': event.get('id'), 'name': event.get('name'), 'disaster_start_date': event.get('disaster_start_date'), 'disaster_type': (event.get('dtype') or {}).get('name'), 'countries': [{'id': x.get('id'), 'name': x.get('name'), 'iso': x.get('iso')} for x in event.get('countries', [])], 'num_affected': event.get('num_affected')})
    return {'source': 'IFRC GO public event summaries', 'source_url': BASE + 'event/', 'count': d['count'], 'next': d['next'], 'results': out, 'note': 'IFRC platform event records are not an exhaustive count of national disasters; affected figures and classifications may be incomplete or revised. Redistribution rights have not been verified.'}
