"""NOAA NHC HURDAT2 historical best-track records."""
import release_runtime
import csv, hashlib, io, re
import requests
from bs4 import BeautifulSoup
INDEX = 'https://www.nhc.noaa.gov/data/'
HOST = 'https://www.nhc.noaa.gov'

def _get(url, max_bytes=10000000):
    with requests.get(url, timeout=45, stream=True, allow_redirects=False) as r:
        if r.is_redirect or not r.ok:
            raise RuntimeError('NOAA source request failed: HTTP ' + str(r.status_code))
        out = bytearray()
        for chunk in r.iter_content(65536):
            out.extend(chunk)
            if len(out) > max_bytes:
                raise RuntimeError('NOAA response exceeds size limit')
    return bytes(out)

def catalog():
    html = _get(INDEX, 2000000).decode('utf-8')
    s = BeautifulSoup(html, 'html.parser')
    found = []
    for a in s.select('a[href]'):
        href = a['href']
        if re.fullmatch('/data/hurdat/hurdat2-(?:nepac-)?\\d{4}-\\d{4}-\\d{6}\\.txt', href):
            found.append({'basin': 'pacific' if '-nepac-' in href else 'atlantic', 'url': HOST + href, 'link_text': a.get_text(' ', strip=True)})
    if len(found) != 2 or {x['basin'] for x in found} != {'atlantic', 'pacific'}:
        raise RuntimeError('NOAA HURDAT2 catalogue layout changed')
    return {'source': 'NOAA National Hurricane Center HURDAT2', 'source_info': INDEX, 'items': found, 'note': '历史最佳路径资料并非实时预报；原始覆盖年限以文件名及 NOAA 数据目录为准，可能修订。'}

def storm(storm_id):
    if not isinstance(storm_id, str) or not re.fullmatch('(AL|EP|CP)\\d{6}', storm_id.upper()):
        raise ValueError('Storm ID must be AL/EP/CP plus 2-digit storm number and 4-digit year')
    storm_id = storm_id.upper()
    basin = 'atlantic' if storm_id.startswith('AL') else 'pacific'
    url = next((x['url'] for x in catalog()['items'] if x['basin'] == basin))
    raw = _get(url)
    reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')))
    header = None
    entries = []
    remaining = 0
    for row in reader:
        row = [v.strip() for v in row]
        if row and re.fullmatch('(AL|EP|CP)\\d{6}', row[0]):
            if header is not None:
                break
            if row[0] == storm_id:
                if len(row) < 3 or not row[2].isdigit():
                    raise RuntimeError('Malformed NOAA storm header')
                header = {'id': row[0], 'name_original': row[1], 'record_count': int(row[2])}
                remaining = int(row[2])
        elif header is not None:
            if len(row) < 8 or not re.fullmatch('\\d{8}', row[0]) or (not re.fullmatch('\\d{4}', row[1])):
                raise RuntimeError('Malformed NOAA track row')
            entries.append({'date_utc': row[0], 'time_utc': row[1], 'record_identifier': row[2], 'status_code': row[3], 'latitude_original': row[4], 'longitude_original': row[5], 'max_wind_knots_original': row[6], 'minimum_pressure_mb_original': row[7], 'extra_fields_original': row[8:]})
            remaining -= 1
            if remaining == 0:
                break
    if header is not None and remaining != 0:
        raise RuntimeError('NOAA storm data incomplete')
    return {'source': 'NOAA National Hurricane Center HURDAT2', 'source_url': url, 'source_info': INDEX, 'sha256': hashlib.sha256(raw).hexdigest(), 'file_bytes': len(raw), 'storm': header, 'records': entries, 'note': '事后最佳路径历史分析，不是实时监测或预报；位置及风压字段原样保留，-999 等为缺测标记不是实际气压。风速为节、气压毫巴；除每6小时也有登陆等非标准时刻，点数不是风暴数。文件可能修订。'}
