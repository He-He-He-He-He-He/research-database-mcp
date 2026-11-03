"""NOAA NCEI Storm Events annual detail CSV for US and adjacent waters."""
import release_runtime
import csv
import gzip
import io
import re
import requests
ROOT = 'https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/'
PAGE = 'https://www.ncei.noaa.gov/access/storm-events-database/'

def _load(year):
    r = requests.get(ROOT, timeout=30)
    r.raise_for_status()
    names = sorted(set(re.findall('StormEvents_details-ftp_v1\\.0_d' + str(year) + '_c[0-9]{8}\\.csv\\.gz', r.text)))
    if not names:
        raise ValueError('no official annual details file for year')
    name = names[-1]
    url = ROOT + name
    r = requests.get(url, timeout=60, stream=True)
    r.raise_for_status()
    parts = []
    size = 0
    for b in r.iter_content(65536):
        size += len(b)
        if size > 30000000:
            raise ValueError('compressed file exceeds 30 MB')
        parts.append(b)
    with gzip.GzipFile(fileobj=io.BytesIO(b''.join(parts))) as f:
        raw = f.read(200000001)
    if len(raw) > 200000000:
        raise ValueError('decompressed file exceeds 200 MB')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    if not reader.fieldnames or not {'STATE', 'YEAR', 'EVENT_TYPE', 'EVENT_ID', 'CZ_TIMEZONE'}.issubset(reader.fieldnames):
        raise ValueError('unexpected CSV schema')
    return (url, name, list(reader))

def search(year, state, event='', limit=20, offset=0):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    if any((not isinstance(v, str) or len(v) > 100 for v in (state, event))) or not state.strip():
        raise ValueError('invalid filter')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    url, name, rows = _load(year)
    if any((r.get('YEAR') != str(year) for r in rows)):
        raise ValueError('unexpected year in data')
    selected = [r for r in rows if (r.get('STATE') or '').casefold() == state.casefold() and (not event or (r.get('EVENT_TYPE') or '').casefold() == event.casefold())]
    return {'source': url, 'documentation': PAGE, 'file_version': name, 'total_year_records': len(rows), 'matched': len(selected), 'limit': limit, 'offset': offset, 'rows': selected[offset:offset + limit], 'note': 'NWS reported significant weather events for United States and adjacent waters, not every event or population exposure. Event records and episodes can overlap; fatalities/injuries direct and indirect differ. Preserve local timezone, damage strings and missing values. Source filenames encode extraction dates and data may be revised. Full annual file is downloaded and filtered locally.'}
