"""GDACS official recent-event GeoJSON feed; no disaster forecasts or population estimates."""
import release_runtime
import requests
URL = 'https://www.gdacs.org/gdacsapi/api/Events/geteventlist/EVENTS4APP'

def recent(event_type=None, alert_level=None, limit=20):
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError('limit must be between 1 and 100')
    response = requests.get(URL, timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
        raise ValueError('Unexpected GDACS response')
    features = data['features']
    selected = [f for f in features if (not event_type or f.get('properties', {}).get('eventtype', '').casefold() == event_type.casefold()) and (not alert_level or f.get('properties', {}).get('alertlevel', '').casefold() == alert_level.casefold())]
    return {'source': 'GDACS EVENTS4APP', 'feed_count': len(features), 'matched_count': len(selected), 'returned_count': min(limit, len(selected)), 'features': selected[:limit], 'note': 'Recent feed at most 100 events; filters apply only to returned feed, not the entire historical database. Alert data can be revised.'}
