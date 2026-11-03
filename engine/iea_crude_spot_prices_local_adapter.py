"""Select a bounded slice of locally downloaded IEA crude spot prices."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/end-use-energy-prices'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
REQUIRED = {'DATASET_ID', 'ENERGY_PRODUCT', 'Product', 'CRUDE_TYPE', 'Crude type', 'FREQUENCY', 'Frequency', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT', 'Unit', 'QUALIFIER', 'Qualifier', 'CONF_STATUS'}

def select(path, product, crude_type, frequency, period, unit, limit=10):
    for name, value in [('product', product), ('crude_type', crude_type), ('frequency', frequency), ('unit', unit)]:
        if not isinstance(value, str) or not re.fullmatch('[A-Z0-9_]{1,60}', value):
            raise ValueError(name + ' must be exact uppercase source code')
    if not isinstance(period, str) or not re.fullmatch('[0-9]{4}(?:-(?:[0-9]{2}|Q[1-4]))?', period):
        raise ValueError('period must use source format')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download authorized IEA SPOTCRUDE ZIP first')
    items = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('SPOTCRUDE.csv')
        if info.file_size > 30000000:
            raise ValueError('Unexpected file size')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in reader:
                if row['ENERGY_PRODUCT'] == product and row['CRUDE_TYPE'] == crude_type and (row['FREQUENCY'] == frequency) and (row['TIME_PERIOD'] == period) and (row['UNIT'] == unit):
                    count += 1
                    if len(items) < limit:
                        items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': 'SPOTCRUDE.csv', 'query': {'product': product, 'crude_type': crude_type, 'frequency': frequency, 'period': period, 'unit': unit}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local file matching the expected IEA format, not a live API. Preserve units, frequency and qualifiers. If the source is confirmed as IEA, consult the non-CC license before sharing.'}
