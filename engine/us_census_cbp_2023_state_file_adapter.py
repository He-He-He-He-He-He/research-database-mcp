"""U.S. Census CBP 2023 state-level public CSV archive."""
import release_runtime
import csv, io, re, zipfile
import requests
URL = 'https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23st.zip'

def industry(state, naics='------'):
    if not isinstance(state, str) or not re.fullmatch('[0-9]{2}', state):
        raise ValueError('state must be a two-digit state FIPS code')
    if not isinstance(naics, str) or not re.fullmatch('[0-9-]{6}', naics):
        raise ValueError('naics must be a six-character source code')
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > 20000000:
                raise ValueError('Archive too large')
            chunks.append(chunk)
    with zipfile.ZipFile(io.BytesIO(b''.join(chunks))) as z:
        files = [i for i in z.infolist() if i.filename == 'cbp23st.txt']
        if len(files) != 1 or files[0].file_size > 120000000:
            raise ValueError('Unexpected archive structure')
        with z.open(files[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            expected = {'fipstate', 'naics', 'lfo', 'emp_nf', 'emp', 'qp1_nf', 'qp1', 'ap_nf', 'ap', 'est'}
            if not reader.fieldnames or not expected.issubset(reader.fieldnames):
                raise ValueError('Unexpected source columns')
            rows = [row for row in reader if row['fipstate'] == state and row['naics'] == naics and (row['lfo'] == '-')]
    if len(rows) > 1:
        raise ValueError('Duplicate state all-organization rows')
    return {'source_url': URL, 'source': 'U.S. Census Bureau 2023 CBP state CSV', 'state_fips': state, 'naics': naics, 'items': rows, 'note': 'Establishments with paid employees, not firms. Employment for pay period including March 12; annual payroll in USD thousands; preserve original noise and suppression flags. No returned row does not mean zero.'}
