"""Read user-downloaded IEA world renewables energy balance snapshot locally."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/renewables-information'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
REQUIRED = {'DATASET_ID', 'COUNTRY', 'Country/Region', 'ENERGY_PRODUCT', 'Product', 'ENERGY_BALANCE_FLOW', 'Flow', 'MEASURE', 'Balance measure', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT', 'Unit', 'QUALIFIER', 'Qualifier', 'CONF_STATUS'}

def select(path, country, product, flow, measure, unit, year, limit=10):
    for name, value in [('country', country), ('product', product), ('flow', flow), ('measure', measure), ('unit', unit)]:
        if not isinstance(value, str) or not re.fullmatch('[A-Z0-9_]{1,60}', value):
            raise ValueError(name + ' must be exact uppercase source code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download authorized IEA renewable balance ZIP first')
    items = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('RENWORLDBAL.csv')
        if info.file_size > 250000000:
            raise ValueError('Unexpected file size')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in reader:
                if row['COUNTRY'] == country and row['ENERGY_PRODUCT'] == product and (row['ENERGY_BALANCE_FLOW'] == flow) and (row['MEASURE'] == measure) and (row['UNIT'] == unit) and (row['TIME_PERIOD'] == str(year)):
                    count += 1
                    if len(items) < limit:
                        items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': 'RENWORLDBAL.csv', 'query': {'country': country, 'product': product, 'flow': flow, 'measure': measure, 'unit': unit, 'year': year}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local file matching the expected IEA format, not live API; energy balance signs, measure, units and qualifiers are source-defined. If the source is confirmed as IEA, consult the non-CC license before sharing.'}
