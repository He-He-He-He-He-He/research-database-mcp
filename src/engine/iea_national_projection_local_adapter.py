"""Query one licensed IEA national projection indicator locally."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/energy-projections-of-iea-countries-national-data'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
FIELDS = ('COUNTRY', 'ENERGY_INDICATOR', 'SCENARIO', 'UNIT')
REQUIRED = set(FIELDS) | {'DATASET_ID', 'Indicator', 'Scenario', 'TIME_PERIOD', 'OBS_VALUE', 'QUALIFIER', 'Qualifier', 'BASE_PER', 'CONF_STATUS'}

def select(path, country, indicator, scenario, unit, year, limit=10):
    values = (country, indicator, scenario, unit)
    for name, value in zip(FIELDS, values):
        if not isinstance(value, str) or not re.fullmatch('[A-Z0-9_]{1,60}', value):
            raise ValueError(name + ' must be exact uppercase source code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download authorized IEA SLTINDICEXTEND ZIP first')
    query = dict(zip(FIELDS, values))
    items = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('SLTINDICEXTEND.csv')
        if info.file_size > 100000000:
            raise ValueError('Unexpected file size')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in reader:
                if row['TIME_PERIOD'] == str(year) and all((row[k] == v for k, v in query.items())):
                    count += 1
                    if len(items) < limit:
                        items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': 'SLTINDICEXTEND.csv', 'query': {**query, 'year': year}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local file matching the expected IEA format, not live API. National scenario projections are not observed outcomes; preserve base period and qualifier.'}
