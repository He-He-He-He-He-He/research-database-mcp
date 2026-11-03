"""Met Office official historic monthly station observations."""
import release_runtime
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data'
NOTES = ['Station observations are monthly, not daily or a national average; the source says no allowance has been made for small site changes or instrumentation developments.', 'Raw --- indicates missing, * indicates estimated values, and # can mark sunshine instrument; retain source header and flags. Recent rows may be provisional.', 'tmax and tmin are monthly means of daily maxima and minima in degrees C, af is frost days, rain is total mm, sun is hours. Inspect the source header for station-specific notes.', 'Current files may be revised and do not constitute a historical publication snapshot. Data.gov.uk lists the dataset under the UK Open Government Licence.']

def _get(url):
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    return r

def stations(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('Invalid keyword')
    soup = BeautifulSoup(_get(PAGE).text, 'html.parser')
    rows = []
    for a in soup.select('a[href]'):
        u = urlparse(a['href'])
        m = re.fullmatch('/pub/data/weather/uk/climate/stationdata/([a-z0-9]+)data\\.txt', u.path)
        if u.scheme != 'https' or u.hostname != 'www.metoffice.gov.uk' or (not m):
            continue
        tr = a.find_parent('tr')
        td = tr.find_all('td', recursive=False) if tr else []
        if len(td) < 3:
            raise ValueError('Unexpected Met Office station row')
        rows.append({'code': m.group(1), 'name': td[0].get_text(' ', strip=True), 'coordinates_raw': td[1].get_text(' ', strip=True), 'start_year_raw': td[2].get_text(' ', strip=True), 'url': a['href']})
    if not rows or len({r['code'] for r in rows}) != len(rows):
        raise ValueError('Empty or duplicate Met Office catalogue')
    rows = [r for r in rows if keyword.casefold() in (r['name'] + ' ' + r['code']).casefold()]
    return {'source': PAGE, 'total_matching': len(rows), 'notes': NOTES, 'records': rows}

def observations(code, start, end):
    if not isinstance(code, str) or not re.fullmatch('[a-z0-9]{2,30}', code) or type(start) is not int or (type(end) is not int) or (not 1800 <= start <= end <= 2100):
        raise ValueError('Invalid station code or year range')
    matches = [x for x in stations()['records'] if x['code'] == code]
    if len(matches) != 1:
        raise ValueError('Station not found in official catalogue')
    r = _get(matches[0]['url'])
    lines = r.text.splitlines()
    rows = []
    header = []
    in_data = False
    for line in lines:
        p = line.split()
        if len(p) >= 7 and re.fullmatch('\\d{4}', p[0]) and p[1].isdigit():
            in_data = True
            year, month = (int(p[0]), int(p[1]))
            if not 1 <= month <= 12:
                raise ValueError('Unexpected Met Office month')
            if start <= year <= end:
                rows.append({'year': year, 'month': month, 'tmax_raw': p[2], 'tmin_raw': p[3], 'air_frost_days_raw': p[4], 'rain_mm_raw': p[5], 'sun_hours_raw': p[6], 'additional_flags_raw': ' '.join(p[7:]), 'source_line': line})
        elif not in_data:
            header.append(line)
    if not in_data:
        raise ValueError('No monthly data rows in Met Office file')
    return {'source': matches[0]['url'], 'station': matches[0], 'source_header': header, 'http_last_modified': r.headers.get('Last-Modified'), 'notes': NOTES, 'records': rows}
