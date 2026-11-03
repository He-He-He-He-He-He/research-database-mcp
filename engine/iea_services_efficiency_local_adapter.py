"""Query one exact dimension slice of a locally downloaded IEA services CSV."""
import release_runtime
import csv, re
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/energy-end-uses-and-efficiency-indicators'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
DIMENSIONS = ('COUNTRY', 'MEASURE', 'METRIC', 'SECTOR', 'ENDUSE', 'ENERGY_PRODUCT', 'CORRECTION', 'UNIT')
REQUIRED = set(DIMENSIONS) | {'DATASET_ID', 'TIME_PERIOD', 'OBS_VALUE', 'Qualifier', 'CONF_STATUS'}

def select(path, country, measure, metric, sector, enduse, product, correction, unit, year, limit=10):
    vals = (country, measure, metric, sector, enduse, product, correction, unit)
    for name, v in zip(DIMENSIONS, vals):
        if not isinstance(v, str) or not re.fullmatch('[A-Z0-9_]{1,60}', v):
            raise ValueError(name + ' must be exact uppercase source code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download authorized IEA services CSV first')
    if p.stat().st_size > 200000000:
        raise ValueError('Unexpected file size')
    query = dict(zip(DIMENSIONS, vals))
    items = []
    count = 0
    with p.open(encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f)
        if not REQUIRED.issubset(r.fieldnames or []):
            raise ValueError('Unexpected IEA CSV schema')
        for row in r:
            if row['TIME_PERIOD'] == str(year) and all((row[k] == v for k, v in query.items())):
                count += 1
                if len(items) < limit:
                    items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'query': {**query, 'year': year}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local file matching the expected IEA format, not live API. Preserve units, definitions and qualifiers; If the source is confirmed as IEA, consult the non-CC license before sharing.'}
