"""EEA 2011–2025 bathing-water excellent-quality site indicators."""
import release_runtime
import csv
import io
import re
import zipfile
import requests
URL = 'https://sdi.eea.europa.eu/datashare/s/sWJZjgCqxLzf48a/download'
PAGE = 'https://www.eea.europa.eu/en/datahub/datahubitem-view/d6981ae9-938d-43a9-9c75-c694149f4c8e'
FILE = 'eea_s_eu-sdg-14-40_p_2011-2025_v01_r00.csv'

def _load():
    r = requests.get(URL, timeout=40, stream=True)
    r.raise_for_status()
    buf = []
    size = 0
    for b in r.iter_content(65536):
        size += len(b)
        if size > 10000000:
            raise ValueError('archive too large')
        buf.append(b)
    with zipfile.ZipFile(io.BytesIO(b''.join(buf))) as z:
        hits = [i for i in z.infolist() if i.filename.endswith('/' + FILE)]
        if len(hits) != 1 or hits[0].file_size > 10000000:
            raise ValueError('unexpected archive')
        data = z.read(hits[0]).decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(data, newline='')))
    if not rows or not {'geo', 'time', 'unit', 'dimension', 'obs_value', 'obs_status'}.issubset(rows[0]):
        raise ValueError('unexpected schema')
    return rows

def data(country, start, end, limit=100, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9]{2,8}', country):
        raise ValueError('invalid geo code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 2011 <= start <= end <= 2025:
        raise ValueError('years must be within 2011–2025')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = _load()
    chosen = [x for x in rows if x.get('geo') == country and x.get('time', '').isdigit() and (start <= int(x['time']) <= end)]
    return {'source': URL, 'catalog': PAGE, 'edition': '2011–2025 v01 r00', 'published': '2026-09-04', 'license': 'CC BY 4.0', 'total': len(chosen), 'limit': limit, 'offset': offset, 'rows': chosen[offset:offset + limit], 'note': 'EEA bathing-site counts and shares rated excellent based on intestinal enterococci and E. coli, not general water safety, all waterways, or real-time beach advice. Counts and percentages may share dimension codes; retain unit and dimension label. Excellent sites are a subset of all monitored sites; do not add totals and subsets. Preserve missing values and source status codes. National and regional aggregates may overlap.'}
