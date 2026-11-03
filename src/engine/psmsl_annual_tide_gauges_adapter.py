"""PSMSL station catalogue and observed RLR annual mean sea level."""
import release_runtime
import re
import requests
BASE = 'https://psmsl.org/data/obtaining/'
CATALOGUE = BASE + 'rlr.annual.data/filelist.txt'
NOTES = ['Annual means are relative sea level in millimetres above an arbitrary station-specific RLR datum, not global sea level or sea level above a common datum.', 'Vertical land motion is included; values from different stations cannot be directly compared as absolute elevations.', 'Raw -99999 means missing, never zero. Missing-days flag Y means at least one month missing or at least 30 days missing; check source documentation.', 'Attention flags and station QC flags are retained as text: 001 indicates caution, 010 marks mean tidal level, and 011 combines both.', 'PSMSL may revise its records; consult the station documentation and cite both the data set and recommended publication.']

def _get(url):
    r = requests.get(url, timeout=45, headers={'User-Agent': 'ZJU Research Toolkit/1.0 (academic research)'})
    r.raise_for_status()
    return r.text

def _catalogue():
    rows = []
    for line in _get(CATALOGUE).splitlines():
        p = [v.strip() for v in line.split(';')]
        if len(p) != 7 or not p[0].isdigit() or p[6] not in ('Y', 'N'):
            raise ValueError('Unexpected PSMSL station catalogue row')
        rows.append({'id': int(p[0]), 'latitude': float(p[1]), 'longitude': float(p[2]), 'latitude_raw': p[1], 'longitude_raw': p[2], 'name': p[3], 'coastline_code': p[4], 'station_code': p[5], 'quality_control_flag': p[6]})
    if not rows:
        raise ValueError('Empty PSMSL catalogue')
    return rows

def stations(keyword='', offset=0, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(offset) is not int or (offset < 0) or (type(limit) is not int) or (not 1 <= limit <= 100):
        raise ValueError('Invalid keyword, offset or limit')
    matches = [s for s in _catalogue() if keyword.casefold() in s['name'].casefold()]
    return {'source': CATALOGUE, 'total': len(matches), 'offset': offset, 'returned': len(matches[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(matches) else None, 'truncated': offset + limit < len(matches), 'notes': NOTES + ['The catalogue is fetched anew each request; station ordering may change when the source updates.'], 'records': matches[offset:offset + limit]}

def annual(station_id, start, end):
    if not re.fullmatch('\\d{1,6}', str(station_id)) or int(station_id) < 1:
        raise ValueError('station ID must be a positive integer')
    if type(start) is not int or type(end) is not int or (not 1700 <= start <= end <= 2100):
        raise ValueError('invalid year range')
    sid = int(station_id)
    matches = [row for row in _catalogue() if row['id'] == sid]
    if len(matches) != 1:
        raise ValueError('station not found in RLR annual catalogue')
    url = BASE + f'rlr.annual.data/{sid}.rlrdata'
    records = []
    lines = _get(url).splitlines()
    if not lines:
        raise ValueError('Empty PSMSL station data')
    for line in lines:
        p = [v.strip() for v in line.split(';')]
        if len(p) != 4 or p[2] not in ('Y', 'N') or (not re.fullmatch('[0-7]{3}', p[3])):
            raise ValueError('Unexpected PSMSL annual data row')
        year, value = (int(p[0]), int(p[1]))
        if start <= year <= end:
            records.append({'year': year, 'mean_sea_level_mm_raw': value, 'is_missing': value == -99999, 'missing_days_flag': p[2], 'attention_flag': p[3]})
    return {'source': url, 'catalogue_source': CATALOGUE, 'station': matches[0], 'station_page': BASE + f'stations/{sid}.php', 'station_documentation': BASE + f'docu.psmsl/{sid}.txt', 'notes': NOTES, 'records': records}
