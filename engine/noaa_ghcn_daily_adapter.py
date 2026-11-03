"""NOAA GHCN-Daily global station inventory and daily observations."""
import release_runtime
import argparse, calendar, json, math, re, requests
BASE = 'https://www.ncei.noaa.gov/pub/data/ghcn/daily/'
UNITS = {'TMAX': '0.1 deg C', 'TMIN': '0.1 deg C', 'TAVG': '0.1 deg C', 'PRCP': '0.1 mm', 'SNOW': 'mm', 'SNWD': 'mm', 'AWND': '0.1 m/s', 'RHAV': 'percent'}

def fetch(path):
    with requests.get(BASE + path, timeout=60, stream=True) as r:
        r.raise_for_status()
        data = []
        n = 0
        for c in r.iter_content(65536):
            n += len(c)
            if n > 20000000:
                raise ValueError('file exceeds 20 MB')
            data.append(c)
    return b''.join(data).decode('utf-8')

def stations(keyword, limit=50):
    if not isinstance(keyword, str) or len(keyword.strip()) < 2:
        raise ValueError('keyword must contain at least 2 characters')
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    rows = []
    count = 0
    for line in fetch('ghcnd-stations.txt').splitlines():
        if keyword.upper() not in line.upper():
            continue
        count += 1
        if len(rows) < limit:
            rows.append({'id': line[:11], 'latitude': line[12:20].strip(), 'longitude': line[21:30].strip(), 'elevation_m': line[31:37].strip(), 'state': line[38:40].strip(), 'name': line[41:71].strip(), 'gsn_flag': line[72:75].strip(), 'hcn_flag': line[76:79].strip(), 'wmo_id': line[80:85].strip()})
    return {'source': BASE + 'ghcnd-stations.txt', 'matched_count': count, 'records': rows}

def countries(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    result = []
    for line in fetch('ghcnd-countries.txt').splitlines():
        code = line[:2]
        name = line[3:].strip()
        if not re.fullmatch('[A-Z]{2}', code) or not name:
            raise ValueError('invalid NOAA country row')
        if keyword.casefold() in (code + ' ' + name).casefold():
            result.append({'code': code, 'name': name})
    return {'source': BASE + 'ghcnd-countries.txt', 'count': len(result), 'countries': result, 'note': 'NOAA 使用 GHCN 国家代码，不保证等同 ISO 代码。'}

def stations_search(keyword='', country='', bbox=None, limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if not isinstance(country, str) or (country and (not re.fullmatch('[A-Z]{2}', country))):
        raise ValueError('country must be a NOAA 2-letter code')
    if type(limit) is not int or not 1 <= limit <= 1000 or type(offset) is not int or (offset < 0):
        raise ValueError('invalid offset or limit')
    if bbox is not None:
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4 or any((isinstance(x, bool) or not isinstance(x, (int, float)) or (not math.isfinite(x)) for x in bbox)):
            raise ValueError('bbox requires west south east north')
        west, south, east, north = bbox
        if not -180 <= west < east <= 180 or not -90 <= south < north <= 90:
            raise ValueError('invalid bbox; split antimeridian regions')
    selected = []
    count = 0
    for line in fetch('ghcnd-stations.txt').splitlines():
        if len(line) < 71:
            raise ValueError('malformed station row')
        if country and (not line.startswith(country)):
            continue
        if keyword.casefold() not in line.casefold():
            continue
        try:
            lat = float(line[12:20])
            lon = float(line[21:30])
        except ValueError:
            raise ValueError('invalid station coordinates') from None
        if bbox is not None and (not (west <= lon <= east and south <= lat <= north)):
            continue
        if offset <= count < offset + limit:
            selected.append({'id': line[:11], 'latitude': line[12:20].strip(), 'longitude': line[21:30].strip(), 'elevation_m': line[31:37].strip(), 'state': line[38:40].strip(), 'name': line[41:71].strip(), 'gsn_flag': line[72:75].strip(), 'hcn_flag': line[76:79].strip(), 'wmo_id': line[80:85].strip()})
        count += 1
    return {'source': BASE + 'ghcnd-stations.txt', 'matched_count': count, 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < count else None, 'records': selected, 'note': '筛选整个站点目录，可能包含已停用或特定时期无观测站点；请用站点年份要素目录核验。每次重取，源顺序或内容可能更新导致跨页漏重。国家代码为 NOAA 编码，非保证 ISO。'}

def elements(station, year):
    if not isinstance(station, str) or not re.fullmatch('[A-Z0-9]{11}', station):
        raise ValueError('invalid station ID')
    if type(year) is not int or not 1800 <= year <= 2100:
        raise ValueError('invalid year')
    lines = fetch('all/' + station + '.dly').splitlines()
    codes = sorted({line[17:21] for line in lines if line[11:15] == str(year) and re.fullmatch('[A-Z0-9]{4}', line[17:21])})
    return {'source': BASE + 'all/' + station + '.dly', 'station': station, 'year': year, 'elements': [{'code': c, 'raw_unit': UNITS.get(c)} for c in codes], 'documentation': BASE + 'readme.txt', 'note': 'Codes present in this station-year file; a listed element can contain missing daily records. Unmapped unit is unknown, consult NOAA README.'}

def observations(station, year, element, limit=366):
    if not isinstance(station, str) or not re.fullmatch('[A-Z0-9]{11}', station):
        raise ValueError('invalid station ID')
    if isinstance(year, bool) or not 1800 <= int(year) <= 2100:
        raise ValueError('invalid year')
    if not isinstance(element, str) or not re.fullmatch('[A-Z0-9]{4}', element):
        raise ValueError('element must be a four-character NOAA code')
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    path = 'all/' + station + '.dly'
    rows = []
    count = 0
    for line in fetch(path).splitlines():
        if line[11:15] != str(year) or line[17:21] != element:
            continue
        month = int(line[15:17])
        ndays = calendar.monthrange(int(year), month)[1]
        for day in range(ndays):
            part = line[21 + 8 * day:29 + 8 * day]
            if len(part) != 8:
                raise ValueError('malformed record')
            raw = int(part[:5])
            count += 1
            if len(rows) < limit:
                rows.append({'date': f'{year}-{month:02d}-{day + 1:02d}', 'raw_value': None if raw == -9999 else raw, 'measurement_flag': part[5].strip(), 'quality_flag': part[6].strip(), 'source_flag': part[7].strip()})
    return {'source': BASE + path, 'station': station, 'year': year, 'element': element, 'raw_unit': UNITS.get(element), 'element_documentation': BASE + 'readme.txt', 'matched_count': count, 'records': rows, 'note': 'None means not reported; retain flags and consult NOAA README. Raw values are not rescaled; raw_unit null means not mapped by toolkit, not unitless. Empty year/element does not prove station never measured it.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    x = s.add_parser('stations')
    x.add_argument('keyword')
    x.add_argument('--limit', type=int, default=50)
    x = s.add_parser('data')
    x.add_argument('station')
    x.add_argument('year', type=int)
    x.add_argument('element', choices=sorted(UNITS))
    x.add_argument('--limit', type=int, default=366)
    a = p.parse_args()
    result = stations(a.keyword, a.limit) if a.cmd == 'stations' else observations(a.station, a.year, a.element, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
