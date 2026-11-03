"""Read one user-downloaded IEA OECD electricity balance CSV ZIP locally."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/electricity-information'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
NAME = 'ELEBALANCEOECDONLY.csv'
REQUIRED = {'DATASET_ID', 'COUNTRY', 'Country', 'ENERGY_BALANCE_FLOW', 'Flow', 'ENERGY_PRODUCT', 'Product', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT', 'Unit ', 'QUALIFIER', 'Qualifier', 'CONF_STATUS', 'DECIMALS'}

def select(path, country, flow, product, year, limit=10):
    for name, value in [('country', country), ('flow', flow), ('product', product)]:
        if not isinstance(value, str) or not re.fullmatch('[A-Z0-9_]{1,60}', value):
            raise ValueError(name + ' must be exact uppercase source code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download the authorized IEA electricity ZIP first')
    matches = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo(NAME)
        if info.file_size > 150000000:
            raise ValueError('Unexpected uncompressed file size')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in reader:
                if row['COUNTRY'] == country and row['ENERGY_BALANCE_FLOW'] == flow and (row['ENERGY_PRODUCT'] == product) and (row['TIME_PERIOD'] == str(year)):
                    count += 1
                    if len(matches) < limit:
                        matches.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': NAME, 'query': {'country': country, 'flow': flow, 'product': product, 'year': year}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': matches, 'note': 'Local file matching the expected IEA format, not live API. Source annual values, units and qualifiers remain as supplied. If confirmed as IEA, consult the non-CC license before redistribution; verify snapshot/version and country coverage.'}
