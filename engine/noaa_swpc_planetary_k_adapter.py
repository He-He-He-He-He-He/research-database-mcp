"""NOAA Space Weather Prediction Center recent estimated planetary K data."""
import release_runtime
import requests
URLS = {'3h': 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json', '1m': 'https://services.swpc.noaa.gov/json/planetary_k_index_1m.json'}
NOTES = ['NOAA SWPC near-real-time planetary K values are estimates based on the stations available to its operations centre, not the final official planetary Kp index.', 'The 3-hour product and the one-minute running estimate have different time resolutions and fields; do not merge them as identical series or as forecasts.', 'The product is a short rolling window, may be delayed or revised, and is not a historical archive. Keep the original time tag and station count.', 'K describes geomagnetic activity, not a measurement of an earthquake, temperature, or a location-specific impact.']

def recent(mode='3h', limit=20):
    if mode not in URLS or type(limit) is not int or (not 1 <= limit <= 200):
        raise ValueError('Invalid product or limit')
    r = requests.get(URLS[mode], timeout=45)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or any((not isinstance(x, dict) or 'time_tag' not in x for x in data)):
        raise ValueError('Unexpected NOAA space weather response')
    key = 'Kp' if mode == '3h' else 'estimated_kp'
    if data and any((key not in x for x in data)):
        raise ValueError('Missing NOAA K field')
    if any((data[i]['time_tag'] > data[i + 1]['time_tag'] for i in range(len(data) - 1))):
        raise ValueError('NOAA observations not in chronological order')
    return {'source': URLS[mode], 'methodology': 'https://www.swpc.noaa.gov/sites/default/files/images/u2/TheK-index.pdf', 'product': mode, 'http_last_modified': r.headers.get('Last-Modified'), 'total_available': len(data), 'returned': min(limit, len(data)), 'truncated': len(data) > limit, 'notes': NOTES + ['Only the latest limit records are returned. The rolling source changes across requests; separate requests do not form a stable snapshot.'], 'records': data[-limit:]}
