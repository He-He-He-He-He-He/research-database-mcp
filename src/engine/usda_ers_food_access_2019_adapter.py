"""USDA ERS 2019 Large Retailer Access Map tract data and dictionary."""
import release_runtime
import csv
import hashlib
import io
import re
import zipfile
import requests
URL = 'https://ers.usda.gov/media/5627/2019-large-retailer-access-map-lram-formerly-known-as-the-food-access-research-atlas-fara-data.zip?v=86147'
PAGE = 'https://ers.usda.gov/data-products/food-access-research-atlas/download-the-data'
NOTES = ['The 2019 Large Retailer Access Map is an access estimate for historical census tracts, not a current store directory or direct measurement of individual shopping behaviour.', 'Population and occupied housing fields explicitly named 2010 refer to the 2010 census; other variables have their own source years and definitions. Consult USDA documentation and the included variable dictionary.', 'Low-income/low-access flags apply specific income and distance definitions; they do not establish that an individual household lacks food. Urban and rural thresholds differ.', 'Tract identifiers in the source omit leading zeros in some rows. Matching accepts padded IDs but preserves the exact source value. Null and zero strings remain distinct.']

def _load():
    r = requests.get(URL, timeout=90)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('USDA source is not ZIP')
    z = zipfile.ZipFile(io.BytesIO(r.content))
    required = {'Food Access Research Atlas.csv', 'ReadMe.csv', 'VariableLookup.csv'}
    if not required.issubset(z.namelist()) or any((z.getinfo(n).file_size > 60000000 for n in required)):
        raise ValueError('Unexpected USDA ZIP')
    return (r, z)

def query(state='', county='', tract='', limit=10, offset=0):
    if not isinstance(state, str) or len(state) > 80 or (not isinstance(county, str)) or (len(county) > 100) or (not isinstance(tract, str)) or (tract and (not re.fullmatch('\\d{10,11}', tract))) or (not (state.strip() or tract)) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Supply state or 10-11 digit tract and valid pagination')
    r, z = _load()
    matches = []
    total = 0
    with z.open('Food Access Research Atlas.csv') as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
        if not {'CensusTract', 'State', 'County', 'Urban', 'Pop2010', 'LILATracts_1And10'} <= set(reader.fieldnames or []):
            raise ValueError('Unexpected USDA columns')
        for row in reader:
            if state and row['State'].casefold() != state.casefold():
                continue
            if county and row['County'].casefold() != county.casefold():
                continue
            if tract and row['CensusTract'].lstrip('0') != tract.lstrip('0'):
                continue
            if offset <= total < offset + limit:
                matches.append(row)
            total += 1
        headers = reader.fieldnames
    with z.open('VariableLookup.csv') as raw:
        dictionary = list(csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')))
    readme = z.read('ReadMe.csv').decode('utf-8-sig')
    return {'source': URL, 'documentation': PAGE, 'sha256': hashlib.sha256(r.content).hexdigest(), 'http_last_modified': r.headers.get('Last-Modified'), 'source_readme': readme, 'source_columns': headers, 'variable_dictionary': dictionary, 'total_matching': total, 'offset': offset, 'notes': NOTES, 'records': matches}
