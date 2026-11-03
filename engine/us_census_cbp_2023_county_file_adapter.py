"""U.S. Census 2023 CBP county-level public CSV archive."""
import release_runtime
import csv, io, re, zipfile
import requests
URL = 'https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23co.zip'

def industry(state, county, naics='------'):
    if not isinstance(state, str) or not re.fullmatch('[0-9]{2}', state):
        raise ValueError('state must be two-digit FIPS')
    if not isinstance(county, str) or not re.fullmatch('[0-9]{3}', county):
        raise ValueError('county must be three-digit FIPS')
    if not isinstance(naics, str) or not re.fullmatch('[0-9-]{6}', naics):
        raise ValueError('naics must be six-character source code')
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 20000000:
                raise ValueError('Archive too large')
            chunks.append(chunk)
    with zipfile.ZipFile(io.BytesIO(b''.join(chunks))) as z:
        files = [i for i in z.infolist() if i.filename == 'cbp23co.txt']
        if len(files) != 1 or files[0].file_size > 150000000:
            raise ValueError('Unexpected archive structure')
        with z.open(files[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            expected = {'fipstate', 'fipscty', 'naics', 'emp_nf', 'emp', 'qp1_nf', 'qp1', 'ap_nf', 'ap', 'est'}
            if not reader.fieldnames or not expected.issubset(reader.fieldnames):
                raise ValueError('Unexpected source columns')
            rows = [row for row in reader if row['fipstate'] == state and row['fipscty'] == county and (row['naics'] == naics)]
    if len(rows) > 1:
        raise ValueError('Unexpected duplicate county-industry rows')
    return {'source_url': URL, 'source': 'U.S. Census Bureau 2023 CBP county CSV', 'state_fips': state, 'county_fips': county, 'naics': naics, 'items': rows, 'note': 'Paid-employee establishments, not firms. Employment for pay period including March 12; annual payroll in USD thousands. Preserve suppression and noise flags; a missing row is not zero.'}
