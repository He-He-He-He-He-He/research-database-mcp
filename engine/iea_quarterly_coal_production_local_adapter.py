"""Bounded local read of the IEA quarterly coal production ZIP."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/quarterly-coal-statistics'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
FIELDS = ('COUNTRY', 'ENERGY_BALANCE_FLOW', 'ENERGY_PRODUCT', 'UNIT')
REQUIRED = set(FIELDS) | {'DATASET_ID', 'Country', 'Flow', 'Coal product', 'TIME_PERIOD', 'FREQUENCY', 'OBS_VALUE', 'Qualifier', 'CONF_STATUS'}

def select(path, country, flow, product, unit, period, limit=10):
    vals = (country, flow, product, unit)
    for name, v in zip(FIELDS, vals):
        if not isinstance(v, str) or not re.fullmatch('[A-Z0-9_]{1,60}', v):
            raise ValueError(name + ' must be exact uppercase source code')
    if not isinstance(period, str) or not re.fullmatch('[0-9]{4}-Q[1-4]', period):
        raise ValueError('period must be YYYY-Q1 through YYYY-Q4')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download IEA quarterly coal production ZIP first')
    q = dict(zip(FIELDS, vals))
    items = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('CST.csv')
        if info.file_size > 20000000:
            raise ValueError('Unexpected file size')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in reader:
                if row['TIME_PERIOD'] == period and all((row[k] == v for k, v in q.items())):
                    count += 1
                    if len(items) < limit:
                        items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': 'CST.csv', 'query': {**q, 'period': period}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local snapshot, not live API; free access does not replace the source license. Preserve units and qualifiers.'}
