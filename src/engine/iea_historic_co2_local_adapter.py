"""Read user-downloaded IEA historic fuel-combustion CO2 snapshot locally."""
import release_runtime
import csv, io, re, zipfile
from pathlib import Path
SOURCE = 'https://www.iea.org/data-and-statistics/data-product/greenhouse-gas-emissions-from-energy'
LICENSE = 'https://www.iea.org/terms/terms-of-use-for-non-cc-material'
REQUIRED = {'DATASET_ID', 'COUNTRY', 'Country', 'EMISSIONS_BALANCE_FLOW', 'Flow', 'ENERGY_PRODUCT', 'Energy Product', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT', 'Unit', 'QUALIFIER', 'Qualifier', 'CONF_STATUS'}

def select(path, country, year, limit=10):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9_]{1,60}', country):
        raise ValueError('country must be exact uppercase source code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1751 <= year <= 2100):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.expandpath(Path(path))
    if not p.is_file():
        raise FileNotFoundError('Download authorized IEA historical emissions ZIP first')
    items = []
    count = 0
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('CO2TIMEEXP.csv')
        if info.file_size > 10000000:
            raise ValueError('Unexpected file size')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Unexpected IEA CSV schema')
            for row in reader:
                if row['COUNTRY'] == country and row['TIME_PERIOD'] == str(year):
                    count += 1
                    if len(items) < limit:
                        items.append(row)
    return {'source_url': None, 'license_url': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(p), 'member': 'CO2TIMEEXP.csv', 'query': {'country': country, 'year': year}, 'provenance_note': 'Local file provenance, version and license are unverified; reference URLs describe the expected source only.', 'match_count': count, 'items': items, 'note': 'Local file matching the expected IEA format of CO2 from fuel combustion, not total GHG or real-time API. Check unit and qualifier; If the source is confirmed as IEA, consult the non-CC license before sharing.'}
