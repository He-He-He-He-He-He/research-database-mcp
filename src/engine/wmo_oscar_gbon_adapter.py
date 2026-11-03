"""WMO OSCAR/Surface global basic observing network station metadata."""
import release_runtime
import re
import requests
URL = 'https://oscar.wmo.int/surface/rest/api/search/station'
DOC = 'https://public.wmo.int/sites/default/files/2024-01/Klausen_Application_of_WIGOS_metadata_WHOS_Training_SAVA_2024.pdf'

def stations(code, territory, offset=0, limit=20):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{3}', code):
        raise ValueError('code must be three alphabetic WMO territory characters')
    if not isinstance(territory, str) or not territory.strip():
        raise ValueError('expected territory name is required')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('limit must be 1–500')
    p = {'territoryName': code.upper(), 'programAffiliation': 'GBON'}
    r = requests.get(URL, params=p, timeout=60)
    r.raise_for_status()
    j = r.json()
    rows = j.get('stationSearchResults')
    if not isinstance(rows, list) or not isinstance(j.get('totalCount'), int):
        raise ValueError('unexpected WMO response')
    if j.get('pageCount') != 1 or len(rows) != j['totalCount']:
        raise ValueError('upstream results incomplete; pagination unsupported')
    if any((str(row.get('territory') or '').strip().casefold() != territory.strip().casefold() for row in rows)):
        raise ValueError('source territory did not match supplied name; WMO may have ignored an invalid code')
    if any((not re.search('(?:^|,)\\s*GBON(?:\\s*:|\\s*,|\\s*$)', str(row.get('stationProgramsDeclaredStatuses') or '')) for row in rows)):
        raise ValueError('source returned a station without a declared GBON program; filter may not have applied')
    return {'source': URL, 'documentation': DOC, 'request': p, 'expected_territory': territory, 'total': j['totalCount'], 'offset': offset, 'limit': limit, 'rows': rows[offset:offset + limit], 'notes': ['Station metadata, not weather observations or verified measurements. GBON declared and assessed statuses can differ; closed/unknown entries are preserved.', 'WMO documents that invalid classifications may be ignored; returned territory and GBON declaration are checked, but zero rows cannot prove whether a code was accepted.', 'Coordinates and elevation are source values; verify precise units and datum against station metadata before spatial analysis. Source snapshot timestamp was not supplied.', 'All matched records are requested from WMO and locally paged; oversized or incomplete upstream responses are rejected.']}
