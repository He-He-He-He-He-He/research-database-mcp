"""Read AUDA-NEPAD public homepage timeline map data (not its API-key-only API)."""
import release_runtime
import json
import re
import requests
URL = 'https://aid.nepad.org/aid/'
DOC = 'https://aid.nepad.org/aid/public/api-docs.php'

def projects(country='', sector='', keyword='', offset=0, limit=20):
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('limit must be 1–500')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    m = re.search('\\bconst\\s+tlData\\s*=\\s*(\\[.*?\\]);', r.text, re.S)
    if not m:
        raise ValueError('public timeline data unavailable or page structure changed')
    values = json.loads(m.group(1))
    if not isinstance(values, list) or not all((isinstance(v, dict) for v in values)):
        raise ValueError('unexpected public timeline format')

    def match(row):
        if country and str(row.get('host_country') or '').casefold() != country.strip().casefold():
            return False
        if sector and str(row.get('sector_name') or '').casefold() != sector.strip().casefold():
            return False
        if keyword and keyword.strip().casefold() not in str(row.get('project_name') or '').casefold():
            return False
        return True
    selected = [r for r in values if match(r)]
    return {'source': URL, 'api_documentation': DOC, 'total_map_rows': len(values), 'total_matches': len(selected), 'offset': offset, 'limit': limit, 'rows': selected[offset:offset + limit], 'notes': ['This reads data already embedded in the public homepage timeline map, not the separate key-protected full API; it is a map subset and is not a complete project catalogue.', 'Country matches host_country only; cross-border projects with another host can be missed. first_year and latest_stage are raw map fields, not independently verified completion dates.', 'Coordinates and WKT geometry are as published and are not a guarantee of accurate location or boundaries; project status and data freshness require verification.', 'The organization offers a distinct documented API that requires registration and an API key.']}
