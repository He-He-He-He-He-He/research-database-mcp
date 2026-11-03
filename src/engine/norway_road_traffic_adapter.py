"""Norway Public Roads Administration traffic stations and annual AADT."""
import release_runtime
import json
import re
import requests
URL = 'https://trafikkdata-api.atlas.vegvesen.no/'
NOTES = ['Norwegian Public Roads Administration traffic monitoring: data are aggregated vehicle counts at individual registration points, not all roads or all transport modes.', 'Annual average daily traffic is a calculated vehicles-per-day figure with quality filtering, not annual total, vehicles per hour or a real-time count. Returned coverage, uncertainty and confidence fields must be checked.', 'Null quality fields and missing years do not mean zero; monitoring sites, methods and road references can change. Current revised values do not prove historical snapshot availability.', 'Use is subject to the Norwegian Licence for Open Government Data (NLOD); acknowledge the source and applicable conditions.']

def _query(query, variables):
    with requests.post(URL, json={'query': query, 'variables': variables}, timeout=45, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 10000000:
                raise ValueError('response too large')
    j = json.loads(raw)
    if not isinstance(j, dict) or j.get('errors') or (not isinstance(j.get('data'), dict)):
        raise ValueError('Traffic API response error: ' + str(j.get('errors', 'invalid response'))[:400])
    return j['data']

def stations(county, road='E', limit=20):
    if type(county) is not int or not 1 <= county <= 99 or road not in ('E', 'R', 'F') or (type(limit) is not int) or (not 1 <= limit <= 100):
        raise ValueError('Invalid county, road or limit')
    q = 'query { trafficRegistrationPoints(searchQuery: {roadCategoryIds: [' + road + '], countyNumbers: [' + str(county) + ']}) { id name location { coordinates { latLon { lat lon } } } } }'
    data = _query(q, {})
    p = data.get('trafficRegistrationPoints')
    if not isinstance(p, list):
        raise ValueError('Unexpected station response')
    return {'source': URL, 'county': county, 'road_category': road, 'total_returned_by_source': len(p), 'shown': min(limit, len(p)), 'notes': NOTES, 'stations': p[:limit]}

def annual(point):
    if not isinstance(point, str) or not re.fullmatch('[A-Za-z0-9]{4,30}', point):
        raise ValueError('Invalid traffic station ID')
    q = 'query($id:String!){ trafficData(trafficRegistrationPointId:$id) { volume { average { daily { byYear { year total { volume { average correctedStandardError standardDeviation confidenceInterval { confidenceLevel confidenceWidth lowerBound upperBound } } coverage { percentage unit included { percentage numerator denominator } uncertain { percentage numerator denominator } unavailable { percentage numerator denominator } } } } } } } } }'
    data = _query(q, {'id': point})
    t = data.get('trafficData')
    if not isinstance(t, dict):
        raise ValueError('No traffic data for this point')
    return {'source': URL, 'station_id': point, 'notes': NOTES, 'data': t}
