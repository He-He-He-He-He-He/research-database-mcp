"""UCDP/PRIO conflict-year records, annual dataset v26.1."""
import release_runtime
import csv
import io
import zipfile
import requests
URL = 'https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip'
MEMBER = 'UcdpPrioConflict_v26_1.csv'

def query(*, location=None, year_from=1946, year_to=2025, limit=100):
    if not 1946 <= year_from <= year_to <= 2025 or not 1 <= limit <= 500:
        raise ValueError('year range must lie in 1946..2025; limit 1..500')
    r = requests.get(URL, stream=True, timeout=30)
    r.raise_for_status()
    with r:
        data = r.raw.read(2000001, decode_content=True)
    if len(data) > 2000000:
        raise ValueError('compressed dataset exceeds limit')
    out = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        info = z.getinfo(MEMBER)
        if info.file_size > 20000000:
            raise ValueError('uncompressed dataset exceeds limit')
        with io.TextIOWrapper(z.open(info), encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                if not year_from <= int(row['year']) <= year_to:
                    continue
                if location and location.casefold() not in [s.strip().casefold() for s in row['location'].split(',')]:
                    continue
                out.append(row)
    return {'source': 'UCDP/PRIO Armed Conflict Dataset v26.1', 'url': URL, 'coverage': '1946–2025, state-based conflict-years', 'total_matches': len(out), 'returned': len(out[:limit]), 'records': out[:limit], 'note': 'Research dataset, not official UN statistics. Intensity 2 indicates at least 1,000 battle-related deaths in that year, not an exact count; location lists states involved, not necessarily event sites. Cite UCDP/PRIO and consult methodology.'}
