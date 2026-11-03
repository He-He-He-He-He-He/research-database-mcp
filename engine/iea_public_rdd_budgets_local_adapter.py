"""Bounded local read of IEA public energy technology RD&D budgets."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/energy-technology-rd-and-d-budget-database-2'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
FIELDS = ('COUNTRY', 'RDD_SECTOR', 'RDD_TYPE', 'RDD_TECH', 'UNIT')
REQUIRED = set(FIELDS) | {'DATASET_ID', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MULT', 'Unit multiplier', 'QUALIFIER', 'Qualifier', 'CONF_STATUS'}

def select(path, country, sector, kind, technology, unit, year, limit=10):
    vals = (country, sector, kind, technology, unit)
    for name, v in zip(FIELDS, vals):
        if not isinstance(v, str) or not re.fullmatch('[A-Z0-9_]{1,60}', v):
            raise ValueError(name + ' must be exact uppercase source code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download IEA public RD&D ZIP first')
    q = dict(zip(FIELDS, vals))
    items = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('RDDPUBLIC.csv')
        if info.file_size > 400000000:
            raise ValueError('Unexpected file size')
        with z.open(info) as raw:
            r = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(r.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in r:
                if row['TIME_PERIOD'] == str(year) and all((row[k] == v for k, v in q.items())):
                    count += 1
                    if len(items) < limit:
                        items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': 'RDDPUBLIC.csv', 'query': {**q, 'year': year}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local snapshot, not live API. Retain unit multiplier and qualifier; free access does not replace source license.'}
