"""EUROCONTROL airport traffic annual CSV; daily IFR movements."""
import release_runtime
import csv
import io
import re
import requests
from datetime import date
ROOT = 'https://www.eurocontrol.int/performance/data/download/csv/airport_traffic_'
DOC = 'https://ansperformance.eu/reference/dataset/airport-traffic/'
MAX = 20000000

def _load(year):
    url = ROOT + str(year) + '.csv'
    r = requests.get(url, timeout=50, stream=True)
    r.raise_for_status()
    parts = []
    size = 0
    for part in r.iter_content(65536):
        size += len(part)
        if size > MAX:
            raise ValueError('CSV exceeds 20 MB')
        parts.append(part)
    reader = csv.DictReader(io.StringIO(b''.join(parts).decode('utf-8-sig'), newline=''))
    if not reader.fieldnames or not {'FLT_DATE', 'APT_ICAO', 'FLT_DEP_1', 'FLT_TOT_IFR_2'}.issubset(reader.fieldnames):
        raise ValueError('unexpected CSV schema')
    return (url, list(reader))

def traffic(airport, start, end, limit=100, offset=0):
    if not isinstance(airport, str) or not re.fullmatch('[A-Z]{4}', airport):
        raise ValueError('airport must be ICAO four-letter code')
    try:
        a = date.fromisoformat(start)
        b = date.fromisoformat(end)
    except (TypeError, ValueError):
        raise ValueError('dates must be YYYY-MM-DD')
    if a > b or a.year != b.year or a.year < 2016:
        raise ValueError('date range must be within one year from 2016')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    url, rows = _load(a.year)
    chosen = [r for r in rows if r.get('APT_ICAO') == airport and start <= r.get('FLT_DATE', '') <= end]
    return {'source': url, 'documentation': DOC, 'airport': airport, 'matched': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'Daily IFR aircraft arrivals and departures, not passenger counts or all flights. Fields ending _1 are Network Manager counts; _IFR_2 are airport operator counts for the same movements and must not be added to _1. Totals already include arrivals and departures. Blank fields remain blank; current-year data may be incomplete or revised. Country and airport coverage limited to source. Yearly CSV downloaded before local filtering.'}
