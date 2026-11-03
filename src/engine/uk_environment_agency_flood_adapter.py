"""Environment Agency (England) public flood monitoring beta API."""
import release_runtime
import re
import requests
BASE = 'https://environment.data.gov.uk/flood-monitoring/'
NOTES = ['This uses Environment Agency flood and river level data from the real-time data API (Beta). Open Government Licence v3.0.', 'The service is not guaranteed for safety-critical applications. Verify current warnings with the official warning service; no returned alert does not prove safety.', 'Measurements may arrive late or be revised. A station may report multiple measures; inspect each measure type, unit, timestamp and local datum. Missing value is not zero.', 'Recent readings coverage is limited, generally up to four weeks. A page reaching the requested limit may be truncated.']

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or not isinstance(j.get('items'), (list, dict)):
        raise ValueError('Unexpected Environment Agency result')
    return j

def stations(town, limit=20, offset=0):
    if not isinstance(town, str) or not town.strip() or len(town) > 80 or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid station query')
    j = _get('id/stations', {'town': town, '_limit': limit, '_offset': offset})
    rows = j['items']
    if not isinstance(rows, list) or len(rows) > limit:
        raise ValueError('Unexpected station list')
    return {'source': BASE + 'id/stations', 'query': {'town': town, 'limit': limit, 'offset': offset}, 'meta': j.get('meta'), 'may_be_truncated': len(rows) == limit, 'notes': NOTES, 'records': rows}

def readings(station, limit=20):
    if not isinstance(station, str) or not re.fullmatch('[A-Za-z0-9_-]{1,40}', station) or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('Invalid station or limit')
    path = 'id/stations/' + station + '/readings'
    j = _get(path, {'_limit': limit, '_sorted': '', '_view': 'full'})
    rows = j['items']
    if not isinstance(rows, list) or len(rows) > limit:
        raise ValueError('Unexpected readings list')
    return {'source': BASE + path, 'station': station, 'meta': j.get('meta'), 'may_be_truncated': len(rows) == limit, 'notes': NOTES, 'records': rows}
