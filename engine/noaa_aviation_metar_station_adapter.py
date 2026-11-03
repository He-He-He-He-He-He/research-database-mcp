"""NOAA Aviation Weather Center public latest METAR station observations."""
import release_runtime
import re
import requests
URL = 'https://aviationweather.gov/api/data/metar'

def latest(stations):
    if not isinstance(stations, (tuple, list)) or not 1 <= len(stations) <= 10:
        raise ValueError('stations must be a list of 1 to 10 ICAO identifiers')
    if any((not isinstance(x, str) or not re.fullmatch('[A-Z0-9]{4}', x) for x in stations)):
        raise ValueError('Each station must be a four-character uppercase ICAO identifier')
    if len(set(stations)) != len(stations):
        raise ValueError('Duplicate station identifier')
    response = requests.get(URL, params={'ids': ','.join(stations), 'format': 'json'}, headers={'User-Agent': 'ZJU-Research-Toolkit/1.0 (personal research)'}, timeout=30)
    response.raise_for_status()
    if len(response.content) > 2000000:
        raise ValueError('Unexpected response size')
    data = [] if response.status_code == 204 or not response.content else response.json()
    if not isinstance(data, list) or any((not isinstance(x, dict) or x.get('icaoId') not in stations for x in data)):
        raise ValueError('Unexpected METAR response')
    found = {x['icaoId'] for x in data}
    return {'source_url': response.url, 'documentation': 'https://aviationweather.gov/data/api/', 'requested_stations': stations, 'stations_without_returned_report': [x for x in stations if x not in found], 'observations': data, 'note': 'Observations are not forecasts; check report time and original METAR. No returned report does not mean no weather. Official API limits requests to 100/min; avoid frequent polling.'}
