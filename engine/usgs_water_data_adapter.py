"""USGS modernized OGC water data API; one result page per request."""
import release_runtime
from urllib.parse import urlsplit
import requests
BASE = 'https://api.waterdata.usgs.gov/ogcapi/v1/collections'

def _get(url, params=None):
    response = requests.get(url, params=params, timeout=40, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    response.raise_for_status()
    data = response.json()
    if data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
        raise ValueError('Unexpected USGS water data response')
    return data

def daily(location, start, end, parameter_code='00060', statistic_id='00003', limit=100):
    if not isinstance(location, str) or not location.strip():
        raise ValueError('location must be a monitoring location identifier')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10000):
        raise ValueError('limit must be from 1 to 10000')
    return _get(BASE + '/daily/items', {'f': 'json', 'monitoring_location_id': location, 'parameter_code': parameter_code, 'statistic_id': statistic_id, 'datetime': f'{start}/{end}', 'limit': limit})

def location(identifier):
    return _get(BASE + '/monitoring-locations/items', {'f': 'json', 'id': identifier, 'limit': 10})

def next_page(previous):
    links = [x['href'] for x in previous.get('links', []) if x.get('rel') == 'next']
    if not links:
        return None
    url = urlsplit(links[0])
    if url.scheme != 'https' or url.netloc != 'api.waterdata.usgs.gov' or (not url.path.startswith('/ogcapi/v1/collections/')) or (not url.path.endswith('/items')):
        raise ValueError('Unexpected next page URL')
    return _get(links[0])
