"""World Bank GFMR 2026 satellite-based country flaring workbook, 2012–2025."""
import release_runtime
import io
import requests
import openpyxl
URL = 'https://thedocs.worldbank.org/en/doc/b34e0c054bb3fe3695e70154c28eef3f-0400072026/related/Flare-volume-and-intensity-estimates-2012-2025.xlsx'
DOC = 'https://www.worldbank.org/en/programs/gasflaringreduction/global-flaring-data'
SHEETS = {'volume': 'Flare volume', 'intensity': 'Flaring intensity', 'oil': 'Oil production'}

def data(kind, country='', start=2012, end=2025, offset=0, limit=20):
    if kind not in SHEETS:
        raise ValueError('unknown kind')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start, end))) or not 2012 <= start <= end <= 2025:
        raise ValueError('year range must be within 2012–2025')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 200):
        raise ValueError('limit must be 1–200')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w[SHEETS[kind]].iter_rows(values_only=True)
        header = list(next(it))
        if header[1:15] != list(range(2012, 2026)):
            raise ValueError('unexpected year headers')
        rows = []
        for row in it:
            if row[0] is None:
                continue
            if country and str(row[0]).strip().casefold() != country.strip().casefold():
                continue
            rows.append({'country': row[0], 'values': {str(year): row[year - 2011] for year in range(start, end + 1)}})
        return {'source': URL, 'documentation': DOC, 'release': '2026', 'kind': kind, 'source_header': header[0], 'unit': {'volume': 'billion cubic metres (bcm)', 'intensity': 'cubic metres of gas per barrel of oil (m3/bbl)', 'oil': 'thousand barrels per day (kbbl/day)'}[kind], 'total_matches': len(rows), 'offset': offset, 'limit': limit, 'rows': rows[offset:offset + limit], 'notes': ['Annual country flaring volumes are satellite-derived estimates calibrated using external data, not direct complete measurements.', 'Flaring intensity is gas volume per barrel of oil; volume, intensity and oil output are distinct measures and are not interchangeable.', '2026 tracker covers 2012–2025 and past values may be revised. Missing cells remain null and are not zero; country names and territorial coverage follow source workbook.']}
    finally:
        w.close()
